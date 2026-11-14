package org.southernnewengland.transitatlas

import org.junit.Assert.*
import org.junit.Test

class NetworkDownloadPlanTest {
    private fun pack(id: String, deps: List<String> = emptyList()) =
        NetworkDownloadPlan.Pack(id, 123L, "a".repeat(64), deps, "Synthetic test geography", "test-v1")

    @Test fun noSelectionMeansNoDownloads() {
        val plan = NetworkDownloadPlan.resolve(emptyList(), mapOf("cttransit" to pack("cttransit")))
        assertTrue(plan.packs.isEmpty())
        assertEquals(0L, plan.totalBytes)
    }

    @Test fun selectedAgenciesOnly() {
        val catalog = mapOf("cttransit" to pack("cttransit"), "pvta" to pack("pvta"))
        val plan = NetworkDownloadPlan.resolve(listOf("cttransit"), catalog)
        assertEquals(listOf("cttransit"), plan.packs.map { it.id })
        assertEquals(123L, plan.totalBytes)
    }

    @Test fun sharedDependencyIsDeduplicated() {
        val catalog = mapOf(
            "cttransit" to pack("cttransit", listOf("shared-streets")),
            "hartford" to pack("hartford", listOf("shared-streets")),
            "shared-streets" to pack("shared-streets")
        )
        val plan = NetworkDownloadPlan.resolve(listOf("cttransit", "hartford"), catalog)
        assertEquals(listOf("shared-streets", "cttransit", "hartford"), plan.packs.map { it.id })
        assertEquals(369L, plan.totalBytes)
    }

    @Test fun unavailableAgencyIsReportedNotInvented() {
        val plan = NetworkDownloadPlan.resolve(listOf("pvta"), emptyMap())
        assertEquals(listOf("pvta"), plan.unavailable)
        assertTrue(plan.packs.isEmpty())
    }

    @Test fun additionalAgencyDependencyRequiresConsent() {
        val catalog = mapOf("cttransit" to pack("cttransit", listOf("pvta")), "pvta" to pack("pvta"))
        assertThrows(IllegalArgumentException::class.java) {
            NetworkDownloadPlan.resolve(listOf("cttransit"), catalog)
        }
    }

    @Test fun missingDependencyIsRejected() {
        assertThrows(IllegalStateException::class.java) {
            NetworkDownloadPlan.resolve(listOf("cttransit"),
                mapOf("cttransit" to pack("cttransit", listOf("shared-streets"))))
        }
    }

    @Test fun cyclesAndTamperedMetadataAreRejected() {
        val catalog = mapOf(
            "cttransit" to pack("cttransit", listOf("shared-a")),
            "shared-a" to pack("shared-a", listOf("cttransit"))
        )
        assertThrows(IllegalArgumentException::class.java) {
            NetworkDownloadPlan.resolve(listOf("cttransit"), catalog)
        }
        val bad = pack("cttransit").copy(sha256 = "not-a-checksum")
        assertThrows(IllegalArgumentException::class.java) {
            NetworkDownloadPlan.resolve(listOf("cttransit"), mapOf("cttransit" to bad))
        }
    }
}
