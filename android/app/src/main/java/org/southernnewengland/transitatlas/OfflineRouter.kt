package org.southernnewengland.transitatlas

import android.database.sqlite.SQLiteDatabase
import java.io.File
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.PriorityQueue
import kotlin.math.*

/** Offline Kotlin timetable router. No network, location, or Android UI dependency. */
internal object OfflineRouter {
    data class Stop(val id: String, val name: String, val lat: Double, val lon: Double)
    data class Link(val from: String, val to: String, val departure: Int, val arrival: Int,
                    val trip: String, val route: String, val sequence: Int)
    data class Transfer(val from: String, val to: String, val seconds: Int, val source: String)
    data class Leg(val from: String, val to: String, val departure: Int, val arrival: Int,
                   val route: String, val source: String)
    data class Result(val arrival: Int, val legs: List<Leg>)
    data class Data(val stops: Map<String, Stop>, val links: List<Link>,
                    val transfers: List<Transfer>, val agencies: Set<String>)

    private val dateFormat = DateTimeFormatter.BASIC_ISO_DATE

    fun read(files: List<File>, day: LocalDate, streetGraph: OfflineStreetGraph? = null): Data {
        val stops = linkedMapOf<String, Stop>()
        val links = mutableListOf<Link>()
        val rules = linkedMapOf<Pair<String, String>, Pair<Int, Int>>()
        val agencies = linkedSetOf<String>()
        val days = listOf(day.minusDays(1), day, day.plusDays(1))
        for (file in files.sortedBy { it.name }) {
            if (!file.isFile) continue
            SQLiteDatabase.openDatabase(file.path, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                db.rawQuery("PRAGMA integrity_check", null).use { c ->
                    require(c.moveToFirst() && c.getString(0) == "ok") { "Invalid offline SQLite: ${file.name}" }
                }
                val localStops = mutableSetOf<String>()
                db.rawQuery("SELECT id,name,lat,lon FROM stops", null).use { c ->
                    while (c.moveToNext()) {
                        val id = c.getString(0)
                        val next = Stop(id, c.getString(1) ?: id, c.getDouble(2), c.getDouble(3))
                        require(stops[id] == null || stops[id] == next) { "Conflicting stop ID: $id" }
                        stops[id] = next
                        localStops.add(id)
                    }
                }
                db.rawQuery("SELECT DISTINCT feed FROM routes", null).use { c ->
                    while (c.moveToNext()) agencies.add(c.getString(0))
                }
                db.rawQuery("SELECT a,b,type,seconds FROM transfers", null).use { c ->
                    while (c.moveToNext()) {
                        val key = c.getString(0) to c.getString(1)
                        val rule = c.getInt(2) to c.getInt(3)
                        require(rules[key] == null || rules[key] == rule) { "Conflicting transfer rule: $key" }
                        rules[key] = rule
                    }
                }
                for ((offset, serviceDay) in days.withIndex()) {
                    val date = serviceDay.format(dateFormat)
                    val weekday = serviceDay.dayOfWeek.value - 1
                    val active = mutableSetOf<String>()
                    db.rawQuery("SELECT service,days FROM calendar WHERE start<=? AND end>=?",
                        arrayOf(date, date)).use { c ->
                        while (c.moveToNext()) {
                            val pattern = c.getString(1) ?: ""
                            if (pattern.length == 7 && pattern[weekday] == '1') active.add(c.getString(0))
                        }
                    }
                    db.rawQuery("SELECT service,type FROM exceptions WHERE date=?", arrayOf(date)).use { c ->
                        while (c.moveToNext()) {
                            if (c.getInt(1) == 1) active.add(c.getString(0))
                            else active.remove(c.getString(0))
                        }
                    }
                    if (active.isEmpty()) continue
                    val shift = (offset - 1) * 86400
                    val placeholders = active.joinToString(",") { "?" }
                    val sql = """SELECT a.stop,b.stop,a.dep,b.arr,t.id,t.route,a.seq
                        FROM trips t JOIN times a ON a.trip=t.id
                        JOIN times b ON b.trip=t.id AND b.seq=a.seq+1
                        WHERE t.service IN ($placeholders) ORDER BY a.dep"""
                    db.rawQuery(sql, active.toTypedArray()).use { c ->
                        while (c.moveToNext()) {
                            val departure = c.getInt(2) + shift
                            val arrival = c.getInt(3) + shift
                            if (arrival < 0 || departure > 172800) continue
                            val a = c.getString(0); val b = c.getString(1)
                            require(a in localStops && b in localStops) { "Broken stop-time references" }
                            require(arrival >= departure) { "Negative scheduled travel time" }
                            links.add(Link(a, b, departure, arrival,
                                serviceDay.toString() + "|" + c.getString(4), c.getString(5), c.getInt(6)))
                        }
                    }
                }
            }
        }
        require(stops.isNotEmpty()) { "Install at least one offline agency pack" }
        val explicit = rules.mapNotNull { (pair, rule) ->
            if (rule.first == 3 || pair.first !in stops || pair.second !in stops) null
            else {
                val a = stops.getValue(pair.first)
                val b = stops.getValue(pair.second)
                val path = if (streetGraph == null) null else try {
                    streetGraph.route(OfflineStreetGraph.Point(a.lat, a.lon),
                        OfflineStreetGraph.Point(b.lat, b.lon))
                } catch (_: OfflineStreetGraph.NoPath) { null }
                if (streetGraph != null && path == null) null
                else Transfer(pair.first, pair.second,
                    max(if (streetGraph != null) path!!.seconds else 60, rule.second),
                    if (streetGraph != null) "osm-graph-estimate" else "official")
            }
        }
        // Explicit forbidden transfers suppress proximity links in that direction.
        val transfers = explicit.toMutableList()
        // Spatial buckets avoid quadratic scans over a regional stop collection.
        val buckets = mutableMapOf<Pair<Int, Int>, MutableList<String>>()
        fun cell(s: Stop) = floor(s.lat * 100).toInt() to floor(s.lon * 100).toInt()
        for ((id, stop) in stops) buckets.getOrPut(cell(stop)) { mutableListOf() }.add(id)
        for ((a, stop) in stops) {
            val (cy, cx) = cell(stop)
            val lonReach = ceil(500.0 / max(1.0, 111000.0 * cos(Math.toRadians(stop.lat))) * 100).toInt() + 1
            for (y in cy - 2..cy + 2) for (x in cx - lonReach..cx + lonReach) {
                for (b in buckets[y to x].orEmpty()) {
                    if (a == b || (a to b) in rules) continue
                    val distance = distance(stop, stops.getValue(b))
                    if (distance <= 500.0) {
                        if (streetGraph == null) {
                            transfers.add(Transfer(a, b, max(60, ceil(distance * 1.3 / 1.25).toInt()), "proximity-estimate"))
                        } else {
                            val target = stops.getValue(b)
                            val path = try {
                                streetGraph.route(OfflineStreetGraph.Point(stop.lat, stop.lon),
                                    OfflineStreetGraph.Point(target.lat, target.lon))
                            } catch (_: OfflineStreetGraph.NoPath) { null }
                            if (path != null) transfers.add(Transfer(a, b, path.seconds, "osm-graph-estimate"))
                        }
                    }
                }
            }
        }
        return Data(stops, links.sortedBy { it.departure }, transfers, agencies)
    }

    private fun distance(a: Stop, b: Stop): Double {
        val lat1 = Math.toRadians(a.lat); val lat2 = Math.toRadians(b.lat)
        val dlat = lat2 - lat1; val dlon = Math.toRadians(b.lon - a.lon)
        val h = sin(dlat / 2).pow(2) + cos(lat1) * cos(lat2) * sin(dlon / 2).pow(2)
        return 12742000 * asin(min(1.0, sqrt(h)))
    }

    /** Connection scan plus walking closure; a 3-minute transfer buffer by default. */
    fun plan(data: Data, origin: String, destination: String, start: Int,
             deadline: Int, buffer: Int = 180): Result? {
        require(origin in data.stops && destination in data.stops) { "Unknown stop" }
        require(start <= deadline && buffer >= 0) { "Invalid planning window" }
        val arrivals = mutableMapOf(origin to start)
        val paths = mutableMapOf(origin to emptyList<Leg>())
        val ready = mutableMapOf(origin to start)
        val outgoing = data.transfers.groupBy { it.from }
        data class Pending(val time: Int, val stop: String, val path: List<Leg>)
        fun relax(at: String, time: Int, path: List<Leg>, initial: Boolean = false) {
            val queue = PriorityQueue(compareBy<Pending> { it.time }.thenBy { it.stop })
            queue.add(Pending(time, at, path))
            while (queue.isNotEmpty()) {
                val item = queue.poll()
                if (item.time > deadline || item.time > (arrivals[item.stop] ?: Int.MAX_VALUE)) continue
                if (item.time < (arrivals[item.stop] ?: Int.MAX_VALUE)) {
                    arrivals[item.stop] = item.time; paths[item.stop] = item.path
                }
                val wait = if (initial && item.stop == at && item.time == time) 0 else buffer
                ready[item.stop] = min(ready[item.stop] ?: Int.MAX_VALUE, item.time + wait)
                for (transfer in outgoing[item.stop].orEmpty()) {
                    val next = item.time + transfer.seconds
                    if (next >= (arrivals[transfer.to] ?: Int.MAX_VALUE) || next > deadline) continue
                    val leg = Leg(item.stop, transfer.to, item.time, next, "walk", transfer.source)
                    val newPath = item.path + leg
                    arrivals[transfer.to] = next
                    paths[transfer.to] = newPath
                    queue.add(Pending(next, transfer.to, newPath))
                }
            }
        }
        relax(origin, start, emptyList(), initial = true)
        val onboard = mutableMapOf<String, Pair<Int, List<Leg>>>()
        for (link in data.links) {
            if (link.departure < start || link.departure > deadline) continue
            if (link.arrival > deadline) continue
            val continued = onboard[link.trip]?.takeIf { it.first == link.sequence - 1 }?.second
            val path = continued ?: if ((ready[link.from] ?: Int.MAX_VALUE) <= link.departure) paths[link.from] else null
            if (path == null) continue
            val leg = Leg(link.from, link.to, link.departure, link.arrival, link.route, "scheduled")
            val newPath = if (path.lastOrNull()?.route == link.route &&
                path.lastOrNull()?.source == "scheduled" && continued != null) {
                path.dropLast(1) + path.last().copy(to = link.to, arrival = link.arrival)
            } else path + leg
            onboard[link.trip] = link.sequence to newPath
            if (link.arrival < (arrivals[link.to] ?: Int.MAX_VALUE)) relax(link.to, link.arrival, newPath)
        }
        return arrivals[destination]?.let { Result(it, paths[destination].orEmpty()) }
    }
}
