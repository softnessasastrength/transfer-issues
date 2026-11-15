package org.southernnewengland.transitatlas

import org.junit.Assert.*
import org.junit.Test

/** Additional deterministic regression cases for native timetable routing. */
class RoutingRegressionTest {
    private val a = OfflineRouter.Stop("ct:a", "Origin", 41.0, -72.0)
    private val b = OfflineRouter.Stop("rail:b", "Interchange", 41.01, -72.0)
    private val c = OfflineRouter.Stop("rail:c", "Destination", 41.02, -72.0)
    private fun data(vararg links: OfflineRouter.Link) = OfflineRouter.Data(
        listOf(a, b, c).associateBy { it.id }, links.toList().sortedBy { it.departure },
        emptyList(), setOf("ct", "rail"))

    @Test fun cannotBoardAtNoPickupStop() {
        val service = data(OfflineRouter.Link(a.id, c.id, 100, 300, "trip", "route", 1, pickup = 1))
        assertNull(OfflineRouter.plan(service, a.id, c.id, 0, 600, buffer = 0))
    }

    @Test fun cannotExitAtNoDropoffStop() {
        val service = data(OfflineRouter.Link(a.id, c.id, 100, 300, "trip", "route", 1, dropoff = 1))
        assertNull(OfflineRouter.plan(service, a.id, c.id, 0, 600, buffer = 0))
    }

    @Test fun stayOnSameTripAcrossNoPickupStop() {
        val service = data(
            OfflineRouter.Link(a.id, b.id, 100, 200, "trip", "route", 1),
            OfflineRouter.Link(b.id, c.id, 220, 320, "trip", "route", 2, pickup = 1)
        )
        val result = OfflineRouter.plan(service, a.id, c.id, 0, 600, buffer = 300)
        assertEquals(320, result!!.arrival)
        assertEquals(1, result.legs.size)
    }

    @Test fun stayOnSameTripAcrossNoDropoffStop() {
        val service = data(
            OfflineRouter.Link(a.id, b.id, 100, 200, "trip", "route", 1, dropoff = 1),
            OfflineRouter.Link(b.id, c.id, 220, 320, "trip", "route", 2)
        )
        assertEquals(320, OfflineRouter.plan(service, a.id, c.id, 0, 600, buffer = 300)!!.arrival)
        assertNull(OfflineRouter.plan(service, a.id, b.id, 0, 600, buffer = 0))
    }

    @Test fun noDepartureAfterDeadline() {
        val service = data(OfflineRouter.Link(a.id, c.id, 601, 700, "trip", "route", 1))
        assertNull(OfflineRouter.plan(service, a.id, c.id, 0, 600, buffer = 0))
    }

    @Test fun sameStopStillPossibleWithNoService() {
        assertEquals(42, OfflineRouter.plan(data(), a.id, a.id, 42, 600)!!.arrival)
    }
}
