package org.southernnewengland.transitatlas

import java.io.File
import java.io.FileOutputStream
import java.nio.file.Files
import java.nio.file.StandardCopyOption

/** Per-agency file activation only. Callers must validate downloads before activate().
 * Never installs another agency, changes selection, or treats recovery as freshness.
 */
class AgencyPackStore(
    private val directory: File,
    private val replace: (File, File) -> Unit = { source, target ->
        Files.move(source.toPath(), target.toPath(),
            StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING)
        Unit
    }
) {
    companion object {
        private val lock = Any() // Includes Activity recreation/overlapping download threads.
        private val agencies = setOf("cttransit", "hartford", "pvta", "amtrak")
    }

    private fun file(agency: String, suffix: String): File {
        require(agency in agencies) { "Unknown agency" }
        check(directory.isDirectory) { "Offline directory unavailable" }
        return File(directory, "$agency$suffix")
    }

    fun staged(agency: String): File {
        val path = file(agency, ".download").let { File(directory, ".${it.name}") }
        check(!Files.isSymbolicLink(path.toPath())) { "Refusing staged pack symlink" }
        return path
    }

    fun <T> withExclusiveAccess(action: () -> T): T = synchronized(lock) { action() }

    private fun copySynced(source: File, target: File) {
        check(source.isFile && source.length() > 0 && !Files.isSymbolicLink(source.toPath())) { "Expected regular pack file" }
        check(!Files.isSymbolicLink(target.toPath())) { "Refusing staging symlink" }
        source.inputStream().use { input ->
            FileOutputStream(target).use { output ->
                input.copyTo(output)
                output.fd.sync()
            }
        }
    }

    /** Preserve active bytes until a verified staged file replaces the active name atomically.
     * Unsupported atomic moves fail closed; no delete/rename fallback creates an active-file gap.
     */
    fun activate(agency: String) = withExclusiveAccess {
        val active = file(agency, ".sqlite")
        val previous = file(agency, ".previous.sqlite")
        val incoming = staged(agency)
        check(incoming.isFile && incoming.length() > 0 && !Files.isSymbolicLink(incoming.toPath())) { "Missing staged pack" }
        check(!Files.isSymbolicLink(active.toPath()) && !Files.isSymbolicLink(previous.toPath())) { "Refusing pack symlink" }
        if (active.exists()) {
            val backupCopy = file(agency, ".rollback-copy")
            copySynced(active, backupCopy)
            replace(backupCopy, previous)
        }
        replace(incoming, active)
    }

    /** Recover legacy interrupted installs only when active is absent. Validate the copy first.
     * Keep previous bytes intact if validation or activation fails, and never replace an active file.
     */
    fun recover(agency: String, validate: (File) -> Unit): Boolean = withExclusiveAccess {
        val active = file(agency, ".sqlite")
        val previous = file(agency, ".previous.sqlite")
        check(!Files.isSymbolicLink(active.toPath())) { "Refusing active pack symlink" }
        if (active.exists()) return@withExclusiveAccess false
        if (!previous.exists()) return@withExclusiveAccess false
        val recovery = file(agency, ".recovery-copy")
        copySynced(previous, recovery)
        validate(recovery)
        replace(recovery, active)
        true
    }
}
