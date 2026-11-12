package org.southernnewengland.transitatlas

import android.app.Activity
import android.app.AlertDialog
import android.os.Bundle
import android.widget.*
import java.io.File
import java.time.LocalDate
import kotlin.concurrent.thread

/** Standalone native offline routing screen, using previously installed packs. */
class OfflinePlannerActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(24, 30, 24, 24) }
        layout.addView(TextView(this).apply { text = "Offline journey planner"; textSize = 24f })
        layout.addView(TextView(this).apply { text = "Stop IDs are available in your downloaded GTFS database. No internet requests." })
        fun field(hintText: String, initial: String = "") = EditText(this).apply {
            hint = hintText
            setSingleLine()
            setText(initial)
            layout.addView(this)
        }
        val from = field("Origin stop ID")
        val to = field("Destination stop ID")
        val day = field("Date YYYY-MM-DD", LocalDate.now().toString())
        val time = field("Departure HH:MM", "10:30")
        val status = TextView(this).apply { text = "Requires installed agency packs"; setPadding(0, 18, 0, 18) }
        layout.addView(status)
        layout.addView(Button(this).apply {
            text = "Calculate offline"
            setOnClickListener {
                val origin = from.text.toString().trim()
                val destination = to.text.toString().trim()
                val date = day.text.toString().trim()
                val hhmm = time.text.toString().trim()
                status.text = "Calculating…"
                thread {
                    try {
                        val pieces = hhmm.split(":")
                        require(pieces.size == 2) { "Use HH:MM" }
                        val hour = pieces[0].toInt()
                        val minute = pieces[1].toInt()
                        require(hour in 0..23 && minute in 0..59) { "Invalid departure time" }
                        val start = hour * 3600 + minute * 60
                        val folder = File(filesDir, "offline")
                        val files = listOf("cttransit", "hartford", "pvta", "amtrak")
                            .map { File(folder, "$it.sqlite") }.filter { it.isFile }
                        val streetFile = File(folder, "streets.sqlite")
                        val graph = if (streetFile.isFile) OfflineStreetGraph.load(streetFile) else null
                        val data = OfflineRouter.read(files, LocalDate.parse(date), graph)
                        val result = OfflineRouter.plan(data, origin, destination, start, start + 18 * 3600)
                        val answer = if (result == null) "No journey in the installed schedule data and 18-hour window."
                        else buildString {
                            append("Arrival at minute ${result.arrival / 60} of the service day\n")
                            for (leg in result.legs) append("${leg.route}: ${leg.from} → ${leg.to} (${leg.departure / 60} to ${leg.arrival / 60} minutes) [${leg.source}]\n")
                        }
                        runOnUiThread {
                            status.text = if (graph != null) "Offline calculation with OSM street graph" else "Offline calculation with geometric walking estimates"
                            AlertDialog.Builder(this@OfflinePlannerActivity).setTitle("Scheduled journey")
                                .setMessage(answer + "\nWalking connections are estimates, not verified sidewalks. Street graph mode is enabled only when streets.sqlite is installed.")
                                .setPositiveButton("Close", null).show()
                        }
                    } catch (e: Exception) {
                        runOnUiThread { status.text = "Cannot calculate: ${e.message}" }
                    }
                }
            }
        })
        layout.addView(Button(this).apply { text = "Back"; setOnClickListener { finish() } })
        setContentView(ScrollView(this).apply { addView(layout) })
    }
}
