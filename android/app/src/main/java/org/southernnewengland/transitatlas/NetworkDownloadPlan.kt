package org.southernnewengland.transitatlas

/** Pure, testable download-plan policy. No network access or Android dependencies. */
object NetworkDownloadPlan {
    data class Pack(
        val id: String,
        val bytes: Long,
        val sha256: String,
        val dependencies: List<String>,
        val scope: String,
        val version: String
    )
    data class Plan(val packs: List<Pack>, val unavailable: List<String>, val totalBytes: Long)

    private val allowedId = Regex("[a-z][a-z0-9_-]{0,63}")
    private val shaPattern = Regex("[a-fA-F0-9]{64}")

    /**
     * Refuse unknown dependencies, malformed metadata, cycles, or unexpected agency additions.
     * Caller must present the returned closure to the user and obtain confirmation.
     */
    fun resolve(selected: List<String>, catalog: Map<String, Pack>): Plan {
        require(selected.distinct().size == selected.size) { "Duplicate agency selection" }
        val ordered = linkedMapOf<String, Pack>()
        val visiting = mutableSetOf<String>()
        fun visit(id: String) {
            require(allowedId.matches(id)) { "Invalid package identifier" }
            val pack = catalog[id] ?: error("Required package unavailable: $id")
            require(pack.id == id && pack.bytes > 0L && shaPattern.matches(pack.sha256)) {
                "Invalid package metadata: $id"
            }
            require(pack.version.isNotBlank() && pack.scope.isNotBlank()) {
                "Missing package version or scope: $id"
            }
            if (id in ordered) return
            require(visiting.add(id)) { "Cyclic package dependencies" }
            for (dependency in pack.dependencies) {
                // Shared infrastructure can be dependencies; never silently add another agency.
                val dependent = catalog[dependency] ?: error("Required dependency unavailable: $dependency")
                require(dependent.id == dependency) { "Dependency identifier mismatch" }
                require(dependency in selected || dependency.startsWith("shared-")) {
                    "Additional agency requires explicit selection: $dependency"
                }
                visit(dependency)
            }
            visiting.remove(id)
            ordered[id] = pack
        }
        val unavailable = selected.filterNot { catalog.containsKey(it) }
        selected.filter { catalog.containsKey(it) }.forEach(::visit)
        var total = 0L
        for (pack in ordered.values) total = Math.addExact(total, pack.bytes)
        return Plan(ordered.values.toList(), unavailable, total)
    }
}
