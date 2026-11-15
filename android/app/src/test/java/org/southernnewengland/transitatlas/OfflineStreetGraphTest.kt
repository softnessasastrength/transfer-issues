package org.southernnewengland.transitatlas

import org.junit.Assert.*
import org.junit.Test

/** Deterministic street graph tests; no Android SQLite or internet needed. */
class OfflineStreetGraphTest {
    private val a = OfflineStreetGraph.Point(41.0, -72.0)
    private val b = OfflineStreetGraph.Point(41.0, -71.999)
    private val c = OfflineStreetGraph.Point(41.0, -71.998)
    private val d = OfflineStreetGraph.Point(41.001, -72.0)
    private fun graph() = OfflineStreetGraph.fixture(
        mapOf(1L to a, 2L to b, 3L to c, 4L to d),
        mapOf(1L to listOf(OfflineStreetGraph.Edge(2, 90.0)),
              2L to listOf(OfflineStreetGraph.Edge(3, 90.0)),
              4L to listOf(OfflineStreetGraph.Edge(1, 110.0))),
        mapOf(1L to listOf(OfflineStreetGraph.Edge(2, 90.0)))
    )

    @Test fun walksDirectedTwoEdgeRoute() {
        val route = graph().route(a, c, snapLimitMeters = 5.0)
        assertEquals(listOf(1L, 2L, 3L), route.nodes)
        assertEquals(180, route.meters)
        assertEquals(144, route.seconds)
    }

    @Test fun refusesReverseOneWay() {
        try {
            graph().route(c, a, snapLimitMeters = 5.0)
            fail("Reverse route must not exist")
        } catch (_: OfflineStreetGraph.NoPath) { }
    }

    @Test fun rejectsMissingCycleConnection() {
        try {
            graph().route(a, c, mode = "cycle", snapLimitMeters = 5.0)
            fail("No cycle connection to node 3")
        } catch (_: OfflineStreetGraph.NoPath) { }
    }

    @Test fun refusesDistantSnap() {
        try {
            graph().route(OfflineStreetGraph.Point(42.0, -72.0), a, snapLimitMeters = 50.0)
            fail("Distant points must not snap")
        } catch (_: OfflineStreetGraph.NoPath) { }
    }

    @Test fun sameNodeHasMinimumSixtySecondEstimate() {
        val result = graph().route(a, a, snapLimitMeters = 5.0)
        assertEquals(listOf(1L), result.nodes)
        assertEquals(60, result.seconds)
    }

    @Test(expected = IllegalArgumentException::class)
    fun unsupportedModeRejected() {
        graph().route(a, b, mode = "scooter")
    }

    @Test fun snapDistancesIncluded() {
        val shifted = OfflineStreetGraph.Point(41.00005, -72.0)
        val route = graph().route(shifted, b, snapLimitMeters = 20.0)
        assertTrue(route.snapStartMeters > 0)
        assertTrue(route.meters > 90)
    }
}
