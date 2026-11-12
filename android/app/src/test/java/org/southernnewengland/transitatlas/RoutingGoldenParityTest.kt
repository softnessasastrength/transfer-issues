package org.southernnewengland.transitatlas

import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

/** Executes the exact same language-neutral cases as Python's test_routing_golden_parity.py. */
class RoutingGoldenParityTest {
    @Test fun sharedGoldenCases() {
        val candidates = listOf(
            File("../../tests/fixtures/routing_golden.psv"),
            File("../tests/fixtures/routing_golden.psv"),
            File("tests/fixtures/routing_golden.psv")
        )
        val fixture = candidates.firstOrNull { it.isFile }
            ?: error("Shared routing golden fixture missing; do not silently skip parity tests")
        val stops = listOf("a", "b", "c").associateWith {
            OfflineRouter.Stop(it, it, 41.0, -72.0)
        }
        for (line in fixture.readLines()) {
            if (line.isBlank() || line.startsWith("#")) continue
            val p = line.split("|")
            require(p.size == 10) { "Invalid golden fixture: $line" }
            val name = p[0]
            val origin = p[1]
            val destination = p[2]
            val start = p[3]
            val deadline = p[4]
            val buffer = p[5]
            val rawLinks = p[6]
            val rawTransfers = p[7]
            val expected = p[8]
            val modes = p[9]
            val links = if (rawLinks == "-") emptyList() else rawLinks.split(";").map { raw ->
                val l = raw.split(",")
                OfflineRouter.Link(l[0], l[1], l[2].toInt(), l[3].toInt(), l[4],
                    l[5], l[6].toInt(), l[7].toInt(), l[8].toInt())
            }.sortedBy { it.departure }
            val transfers = if (rawTransfers == "-") emptyList() else rawTransfers.split(";").map { raw ->
                val t = raw.split(",")
                OfflineRouter.Transfer(t[0], t[1], t[2].toInt(), "synthetic")
            }
            val result = OfflineRouter.plan(
                OfflineRouter.Data(stops, links, transfers, setOf("test")),
                origin, destination, start.toInt(), deadline.toInt(), buffer.toInt()
            )
            val actualArrival = result?.arrival?.toString() ?: "NONE"
            assertEquals("$name arrival", expected, actualArrival)
            if (result != null) {
                val actualModes = result.legs.joinToString(",") { it.route }.ifEmpty { "-" }
                assertEquals("$name legs", modes, actualModes)
            }
        }
    }
}
