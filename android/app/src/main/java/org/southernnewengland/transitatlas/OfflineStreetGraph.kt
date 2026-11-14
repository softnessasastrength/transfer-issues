package org.southernnewengland.transitatlas

import android.database.sqlite.SQLiteDatabase
import java.io.Closeable
import java.io.File
import java.util.PriorityQueue
import kotlin.math.*

/** Same nodes/edges/metadata SQLite contract as scripts/build_street_graph.py. */
internal class OfflineStreetGraph private constructor(
    val nodes: Map<Long, Point>,
    private val edges: Map<String, Map<Long, List<Edge>>>
) {
    data class Point(val lat: Double, val lon: Double)
    data class Edge(val to: Long, val meters: Double)
    data class Route(val nodes: List<Long>, val meters: Int, val seconds: Int,
                     val snapStartMeters: Double, val snapEndMeters: Double)
    class NoPath(message: String) : IllegalArgumentException(message)

    companion object {
        fun load(file: File): OfflineStreetGraph {
            require(file.isFile) { "No offline street graph installed" }
            val nodes = mutableMapOf<Long, Point>()
            val walk = mutableMapOf<Long, MutableList<Edge>>()
            val cycle = mutableMapOf<Long, MutableList<Edge>>()
            SQLiteDatabase.openDatabase(file.path, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                db.rawQuery("PRAGMA integrity_check", null).use { c ->
                    require(c.moveToFirst() && c.getString(0) == "ok") { "Invalid street SQLite" }
                }
                db.rawQuery("SELECT value FROM metadata WHERE key='format'", null).use { c ->
                    require(c.moveToFirst() && c.getString(0) == "atlas-street-v1") { "Unsupported street graph format" }
                }
                db.rawQuery("SELECT id,lat,lon FROM nodes", null).use { c ->
                    while (c.moveToNext()) nodes[c.getLong(0)] = Point(c.getDouble(1), c.getDouble(2))
                }
                db.rawQuery("SELECT src,dst,meters,walk,cycle FROM edges", null).use { c ->
                    while (c.moveToNext()) {
                        val src = c.getLong(0); val dst = c.getLong(1); val distance = c.getDouble(2)
                        require(src in nodes && dst in nodes && distance > 0 && distance.isFinite()) { "Broken street edge" }
                        if (c.getInt(3) == 1) walk.getOrPut(src) { mutableListOf() }.add(Edge(dst, distance))
                        if (c.getInt(4) == 1) cycle.getOrPut(src) { mutableListOf() }.add(Edge(dst, distance))
                    }
                }
            }
            return OfflineStreetGraph(nodes, mapOf("walk" to walk, "cycle" to cycle))
        }

        /** Pure in-memory constructor for deterministic JVM unit tests. */
        fun fixture(nodes: Map<Long, Point>, walk: Map<Long, List<Edge>>,
                    cycle: Map<Long, List<Edge>> = emptyMap()): OfflineStreetGraph =
            OfflineStreetGraph(nodes, mapOf("walk" to walk, "cycle" to cycle))

        fun distance(a: Point, b: Point): Double {
            val la = Math.toRadians(a.lat); val lb = Math.toRadians(b.lat)
            val dy = lb - la; val dx = Math.toRadians(b.lon - a.lon)
            val h = sin(dy / 2).pow(2) + cos(la) * cos(lb) * sin(dx / 2).pow(2)
            return 12742000 * asin(min(1.0, sqrt(h)))
        }
    }

    /** Dijkstra on directed edges. Snaps remain geometric estimates, not verified access paths. */
    fun route(from: Point, to: Point, mode: String = "walk", snapLimitMeters: Double = 100.0): Route {
        require(mode in setOf("walk", "cycle")) { "Unsupported travel mode" }
        require(snapLimitMeters in 0.0..1000.0) { "Invalid snap threshold" }
        val adjacency = edges.getValue(mode)
        val eligible = adjacency.keys + adjacency.values.flatten().map { it.to }
        fun snap(p: Point): Pair<Long, Double> {
            val nearest = eligible.asSequence().mapNotNull { id ->
                nodes[id]?.let { id to distance(p, it) }
            }.minByOrNull { it.second } ?: throw NoPath("No permitted street nodes")
            if (nearest.second > snapLimitMeters) throw NoPath("Stop is too far from a mapped path")
            return nearest
        }
        val (origin, firstSnap) = snap(from)
        val (destination, lastSnap) = snap(to)
        data class State(val cost: Double, val node: Long)
        val queue = PriorityQueue(compareBy<State> { it.cost }.thenBy { it.node })
        val best = mutableMapOf(origin to 0.0)
        val previous = mutableMapOf<Long, Long>()
        queue.add(State(0.0, origin))
        while (queue.isNotEmpty()) {
            val state = queue.poll()
            if (state.cost > (best[state.node] ?: Double.POSITIVE_INFINITY)) continue
            if (state.node == destination) break
            for (edge in adjacency[state.node].orEmpty()) {
                val cost = state.cost + edge.meters
                if (cost < (best[edge.to] ?: Double.POSITIVE_INFINITY)) {
                    best[edge.to] = cost
                    previous[edge.to] = state.node
                    queue.add(State(cost, edge.to))
                }
            }
        }
        val length = best[destination] ?: throw NoPath("No connected permitted street route")
        val path = mutableListOf(destination)
        while (path.last() != origin) {
            path.add(previous[path.last()] ?: throw NoPath("Incomplete street path"))
        }
        path.reverse()
        val total = length + firstSnap + lastSnap
        val speed = if (mode == "walk") 1.25 else 12.0 / 3.6
        return Route(path, ceil(total).toInt(), max(60, ceil(total / speed).toInt()),
            firstSnap, lastSnap)
    }
}
