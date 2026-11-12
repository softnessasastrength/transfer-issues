package org.southernnewengland.transitatlas

import java.util.Locale
import kotlin.math.*

/** Pure, deterministic helpers for native offline stop selection and journey presentation. */
internal object JourneyUiModel {
    fun search(stops: Collection<OfflineRouter.Stop>, query: String, limit: Int = 30): List<OfflineRouter.Stop> {
        val needle = query.trim().lowercase(Locale.ROOT)
        if (needle.isBlank()) return stops.sortedWith(compareBy({ it.name.lowercase(Locale.ROOT) }, { it.id })).take(limit)
        return stops.asSequence().filter {
            it.name.lowercase(Locale.ROOT).contains(needle) || it.id.lowercase(Locale.ROOT).contains(needle)
        }.sortedWith(compareBy<OfflineRouter.Stop>(
            { if (it.name.equals(query.trim(), ignoreCase = true)) 0 else if (it.name.startsWith(query.trim(), ignoreCase = true)) 1 else 2 },
            { it.name.lowercase(Locale.ROOT) }, { it.id }
        )).take(limit).toList()
    }

    fun nearest(stops: Collection<OfflineRouter.Stop>, lat: Double, lon: Double, maxMeters: Double = 2000.0): OfflineRouter.Stop? {
        if (!lat.isFinite() || !lon.isFinite() || lat !in -90.0..90.0 || lon !in -180.0..180.0) return null
        return stops.asSequence().filter { it.lat.isFinite() && it.lon.isFinite() }
            .map { it to OfflineStreetGraph.distance(OfflineStreetGraph.Point(lat, lon),
                OfflineStreetGraph.Point(it.lat, it.lon)) }
            .filter { it.second <= maxMeters }
            .minWithOrNull(compareBy<Pair<OfflineRouter.Stop, Double>>({ it.second }, { it.first.id }))?.first
    }

    fun clock(seconds: Int): String {
        val day = Math.floorDiv(seconds, 86400)
        val normalized = Math.floorMod(seconds, 86400)
        val label = "%02d:%02d".format(Locale.US, normalized / 3600, normalized % 3600 / 60)
        return if (day == 0) label else "$label (${if (day > 0) "+" else ""}$day day)"
    }

    fun itinerary(result: OfflineRouter.Result?, stops: Map<String, OfflineRouter.Stop>): String {
        if (result == null) return "No scheduled journey found for these installed networks."
        val header = "Arrive ${clock(result.arrival)}"
        if (result.legs.isEmpty()) return "$header\nOrigin and destination are the same stop."
        return header + "\n" + result.legs.mapIndexed { index, leg ->
            val from = stops[leg.from]?.name ?: leg.from
            val to = stops[leg.to]?.name ?: leg.to
            val mode = if (leg.route == "walk") "Walk (estimated)" else "Transit ${leg.route}"
            "${index + 1}. $mode\n$from → $to\n${clock(leg.departure)} – ${clock(leg.arrival)}\nSource: ${leg.source}"
        }.joinToString("\n\n")
    }
}
