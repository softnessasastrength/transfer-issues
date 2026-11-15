package org.southernnewengland.transitatlas

import org.junit.Assert.*
import org.junit.Test

/** Synthetic timetable fixtures; no network or real feeds. */
class OfflineRouterTest {
    private val a = OfflineRouter.Stop("ct:a", "CT stop", 41.0, -72.0)
    private val b = OfflineRouter.Stop("rail:b", "Rail stop", 41.0003, -72.0)
    private val c = OfflineRouter.Stop("rail:c", "Rail destination", 42.0, -72.0)

    private fun fixture(transferSeconds: Int = 60) = OfflineRouter.Data(
        stops = listOf(a, b, c).associateBy { it.id },
        links = listOf(OfflineRouter.Link(b.id, c.id, 600, 900, "rail:t", "rail:r", 1)),
        transfers = listOf(OfflineRouter.Transfer(a.id, b.id, transferSeconds, "proximity-estimate")),
        agencies = setOf("cttransit", "hartford")
    )

    @Test fun walkThenBoard() {
        val result = OfflineRouter.plan(fixture(), a.id, c.id, 0, 1200, buffer = 180)
        assertNotNull(result)
        assertEquals(900, result!!.arrival)
        assertEquals(listOf("walk", "rail:r"), result.legs.map { it.route })
    }

    @Test fun transferBufferPreventsBoarding() {
        assertNull(OfflineRouter.plan(fixture(), a.id, c.id, 0, 1200, buffer = 600))
    }

    @Test fun lateArrivalCannotBoard() {
        assertNull(OfflineRouter.plan(fixture(650), a.id, c.id, 0, 1200, buffer = 0))
    }

    @Test fun noConnectionDoesNotInventJourney() {
        assertNull(OfflineRouter.plan(fixture().copy(links = emptyList()), a.id, c.id, 0, 1200))
    }

    @Test fun sameStopReturnsZeroLegJourney() {
        val result = OfflineRouter.plan(fixture(), a.id, a.id, 120, 1200)
        assertEquals(120, result!!.arrival)
        assertTrue(result.legs.isEmpty())
    }

    @Test(expected = IllegalArgumentException::class)
    fun unknownStopRejected() {
        OfflineRouter.plan(fixture(), "not-installed", c.id, 0, 1200)
    }

    @Test fun chainedWalkingTransfers() {
        val d = OfflineRouter.Stop("pvta:d", "PVTA", 41.0006, -72.0)
        val data = fixture().copy(
            stops = listOf(a, b, c, d).associateBy { it.id },
            links = emptyList(),
            transfers = listOf(
                OfflineRouter.Transfer(a.id, b.id, 60, "proximity-estimate"),
                OfflineRouter.Transfer(b.id, d.id, 90, "proximity-estimate")
            )
        )
        val result = OfflineRouter.plan(data, a.id, d.id, 0, 500)
        assertEquals(150, result!!.arrival)
        assertEquals(2, result.legs.size)
    }
}
