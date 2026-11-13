package org.southernnewengland.transitatlas

import java.io.File
import java.io.IOException
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** File lifecycle fixtures only; tests do not certify SQLite contents or Android device behaviour. */
class AgencyPackStoreTest {
    @get:Rule val temporary = TemporaryFolder()
    private val root get() = temporary.root
    private fun active() = File(root, "cttransit.sqlite")
    private fun previous() = File(root, "cttransit.previous.sqlite")
    private fun staged() = File(root, ".cttransit.download")
    private fun move(source: File, target: File) {
        Files.move(source.toPath(), target.toPath(), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING)
    }

    @Test fun firstInstallActivatesOnlyStagedFile() {
        staged().writeText("verified new")
        AgencyPackStore(root).activate("cttransit")
        assertEquals("verified new", active().readText())
        assertFalse(staged().exists())
        assertFalse(previous().exists())
    }

    @Test fun updateKeepsPreviousActiveBytes() {
        active().writeText("working")
        previous().writeText("older")
        staged().writeText("verified new")
        AgencyPackStore(root).activate("cttransit")
        assertEquals("verified new", active().readText())
        assertEquals("working", previous().readText())
    }

    @Test fun failedBackupReplacementLeavesBothOldVersionsUntouched() {
        active().writeText("working")
        previous().writeText("older")
        staged().writeText("verified new")
        val store = AgencyPackStore(root) { _, _ -> throw IOException("backup failure") }
        assertThrows(IOException::class.java) { store.activate("cttransit") }
        assertEquals("working", active().readText())
        assertEquals("older", previous().readText())
        assertEquals("verified new", staged().readText())
    }

    @Test fun failedActivationNeverRemovesActiveName() {
        active().writeText("working")
        staged().writeText("verified new")
        val store = AgencyPackStore(root) { source, target ->
            if (target == active()) throw IOException("activation failure")
            move(source, target)
        }
        assertThrows(IOException::class.java) { store.activate("cttransit") }
        assertEquals("working", active().readText())
        assertEquals("working", previous().readText())
        AgencyPackStore(root).activate("cttransit")
        assertEquals("verified new", active().readText())
    }

    @Test fun backupCopyFailurePreservesActiveAndEarlierBackup() {
        active().writeText("working")
        previous().writeText("older")
        staged().writeText("verified new")
        File(root, "cttransit.rollback-copy").mkdir()
        assertThrows(IOException::class.java) { AgencyPackStore(root).activate("cttransit") }
        assertEquals("working", active().readText())
        assertEquals("older", previous().readText())
    }

    @Test fun recoveryCopyFailurePreservesBackupAndMissingActiveState() {
        previous().writeText("working")
        File(root, "cttransit.recovery-copy").mkdir()
        assertThrows(IOException::class.java) { AgencyPackStore(root).recover("cttransit") {} }
        assertEquals("working", previous().readText())
        assertFalse(active().exists())
    }

    @Test fun unsupportedAtomicMoveFailsWithoutDeleteFallback() {
        active().writeText("working")
        staged().writeText("verified new")
        val store = AgencyPackStore(root) { source, target ->
            throw AtomicMoveNotSupportedException(source.path, target.path, "fixture")
        }
        assertThrows(AtomicMoveNotSupportedException::class.java) { store.activate("cttransit") }
        assertEquals("working", active().readText())
    }

    @Test fun legacyInterruptedActivationRecoversValidatedCopyAndKeepsBackup() {
        previous().writeText("previous verified bytes")
        val store = AgencyPackStore(root)
        assertTrue(store.recover("cttransit") { assertEquals("previous verified bytes", it.readText()) })
        assertEquals(previous().readText(), active().readText())
        assertFalse(store.recover("cttransit") { fail("must not revalidate active pack") })
    }

    @Test fun invalidRecoveryCopyNeverBecomesActive() {
        previous().writeText("invalid SQLite fixture")
        assertThrows(IllegalArgumentException::class.java) {
            AgencyPackStore(root).recover("cttransit") { throw IllegalArgumentException("invalid") }
        }
        assertFalse(active().exists())
        assertEquals("invalid SQLite fixture", previous().readText())
    }

    @Test fun failedRecoveryActivationRetainsBackupForRetry() {
        previous().writeText("working")
        val store = AgencyPackStore(root) { _, _ -> throw IOException("recovery move failed") }
        assertThrows(IOException::class.java) { store.recover("cttransit") {} }
        assertFalse(active().exists())
        assertEquals("working", previous().readText())
        assertTrue(AgencyPackStore(root).recover("cttransit") {})
    }

    @Test fun recoveryDoesNotPromoteUnfinishedDownload() {
        previous().writeText("working")
        staged().writeText("partial unverified")
        AgencyPackStore(root).recover("cttransit") {}
        assertEquals("working", active().readText())
        assertEquals("partial unverified", staged().readText())
    }

    @Test fun existingActivePackIsNeverReplacedDuringRecovery() {
        active().writeText("current")
        previous().writeText("older")
        assertFalse(AgencyPackStore(root).recover("cttransit") { fail("unexpected recovery") })
        assertEquals("current", active().readText())
    }

    @Test fun unknownAgencyIsRejectedWithoutFiles() {
        assertThrows(IllegalArgumentException::class.java) { AgencyPackStore(root).staged("../other") }
        assertTrue(root.listFiles()!!.isEmpty())
    }

    @Test fun exclusiveAccessSerializesDifferentStoreInstances() {
        val executor = Executors.newFixedThreadPool(2)
        val firstEntered = CountDownLatch(1)
        val releaseFirst = CountDownLatch(1)
        val secondAttempted = CountDownLatch(1)
        val secondEntered = CountDownLatch(1)
        try {
            val first = executor.submit {
                AgencyPackStore(root).withExclusiveAccess {
                    firstEntered.countDown()
                    check(releaseFirst.await(5, TimeUnit.SECONDS))
                }
            }
            assertTrue(firstEntered.await(5, TimeUnit.SECONDS))
            val second = executor.submit {
                secondAttempted.countDown()
                AgencyPackStore(root).withExclusiveAccess { secondEntered.countDown() }
            }
            assertTrue(secondAttempted.await(5, TimeUnit.SECONDS))
            assertFalse(secondEntered.await(100, TimeUnit.MILLISECONDS))
            releaseFirst.countDown()
            first.get(5, TimeUnit.SECONDS)
            second.get(5, TimeUnit.SECONDS)
            assertEquals(0L, secondEntered.count)
        } finally {
            releaseFirst.countDown()
            executor.shutdownNow()
        }
    }
}
