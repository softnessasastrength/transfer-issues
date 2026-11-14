package org.southernnewengland.transitatlas

import org.junit.Assert.*
import org.junit.Test

class JourneyUiModelTest {
    private val stops = listOf(
        OfflineRouter.Stop("ct:1", "Hartford Union Station", 41.768, -72.681),
        OfflineRouter.Stop("ct:2", "Hartford Main Street", 41.766, -72.674),
        OfflineRouter.Stop("pvta:1", "Springfield Union Station", 42.106, -72.592)
    )

    @Test fun searchByNameIgnoresCase() {
        assertEquals(2, JourneyUiModel.search(stops, "HARTFORD").size)
    }

    @Test fun searchByIdWorks() {
        assertEquals("pvta:1", JourneyUiModel.search(stops, "pvta:1").single().id)
    }

    @Test fun exactNameRanksFirst() {
        assertEquals("ct:1", JourneyUiModel.search(stops, "Hartford Union Station").first().id)
    }

    @Test fun emptySearchIsStable() {
        assertEquals(2, JourneyUiModel.search(stops, "", limit = 2).size)
    }

    @Test fun nearbyStopIsSelected() {
        assertEquals("ct:1", JourneyUiModel.nearest(stops, 41.768, -72.681)?.id)
    }

    @Test fun farawayTapDoesNotSelectStop() {
        assertNull(JourneyUiModel.nearest(stops, 45.0, -70.0))
    }

    @Test fun clockShowsMidnightRollover() {
        assertEquals("01:00 (+1 day)", JourneyUiModel.clock(90000))
    }

    @Test fun noJourneyHasHonestEmptyState() {
        assertTrue(JourneyUiModel.itinerary(null, stops.associateBy { it.id }).contains("No scheduled journey"))
    }

    @Test fun journeyShowsNamedStopsAndWalkingEstimate() {
        val result = OfflineRouter.Result(600, listOf(
            OfflineRouter.Leg("ct:1", "ct:2", 0, 600, "walk", "osm-graph-estimate")
        ))
        val text = JourneyUiModel.itinerary(result, stops.associateBy { it.id })
        assertTrue(text.contains("Hartford Union Station"))
        assertTrue(text.contains("Walk (estimated)"))
        assertTrue(text.contains("00:10"))
    }
}
