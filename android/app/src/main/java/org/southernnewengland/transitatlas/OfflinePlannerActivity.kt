package org.southernnewengland.transitatlas

import android.app.Activity
import android.database.sqlite.SQLiteDatabase
import android.os.Bundle
import android.view.View
import android.widget.*
import java.io.File
import java.time.LocalDate
import kotlin.concurrent.thread

/** Offline stop-search + map-based journey planning; never uses network or location APIs. */
class OfflinePlannerActivity : Activity() {
    private var stopIndex: List<OfflineRouter.Stop> = emptyList()
    private var origin: OfflineRouter.Stop? = null
    private var destination: OfflineRouter.Stop? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val folder = File(filesDir, "offline")
        val agencyFiles = listOf("cttransit", "hartford", "pvta", "amtrak")
            .map { File(folder, "$it.sqlite") }.filter { it.isFile }
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(20, 20, 20, 20) }
        fun label(text: String, size: Float = 15f) = TextView(this).apply {
            this.text = text; textSize = size; setPadding(0, 8, 0, 8); root.addView(this)
        }
        label("Transit Atlas • Offline journey planner", 23f)
        val status = label("Reading installed stop names…")
        val mode = RadioGroup(this).apply { orientation = RadioGroup.HORIZONTAL }
        val chooseFrom = RadioButton(this).apply { text = "Choose origin"; id = View.generateViewId(); isChecked = true }
        val chooseTo = RadioButton(this).apply { text = "Choose destination"; id = View.generateViewId() }
        mode.addView(chooseFrom); mode.addView(chooseTo); root.addView(mode)
        val selection = label("Origin: not selected\nDestination: not selected")
        val search = EditText(this).apply { hint = "Search station name or stop ID"; setSingleLine() }
        root.addView(search)
        val results = ListView(this)
        root.addView(results, LinearLayout.LayoutParams(-1, 170))
        val map = StopPickerMap(this).apply { minimumHeight = 400 }
        root.addView(map, LinearLayout.LayoutParams(-1, 440))
        val day = EditText(this).apply { hint = "Date YYYY-MM-DD"; setSingleLine(); setText(LocalDate.now().toString()) }
        val time = EditText(this).apply { hint = "Departure HH:MM"; setSingleLine(); setText("10:30") }
        root.addView(day); root.addView(time)
        val journey = label("Select an origin and destination, then calculate.")
        fun selected(stop: OfflineRouter.Stop) {
            if (chooseFrom.isChecked) origin = stop else destination = stop
            map.origin = origin?.id
            map.destination = destination?.id
            selection.text = "Origin: ${origin?.name ?: "not selected"}\nDestination: ${destination?.name ?: "not selected"}"
        }
        map.onStopSelected = { selected(it) }
        mode.setOnCheckedChangeListener { _, id -> map.chooseOrigin = id == chooseFrom.id; map.invalidate() }
        fun updateResults() {
            val matches = JourneyUiModel.search(stopIndex, search.text.toString(), 30)
            results.adapter = ArrayAdapter(this, android.R.layout.simple_list_item_1,
                matches.map { "${it.name} (${it.id})" })
            results.setOnItemClickListener { _, _, position, _ -> selected(matches[position]) }
        }
        search.addTextChangedListener(object : android.text.TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) { updateResults() }
            override fun afterTextChanged(s: android.text.Editable?) {}
        })
        root.addView(Button(this).apply {
            text = "Calculate offline journey"
            setOnClickListener {
                val a = origin?.id; val b = destination?.id
                if (a == null || b == null) { status.text = "Select both stops first"; return@setOnClickListener }
                val dateText = day.text.toString()
                val clockText = time.text.toString()
                status.text = "Calculating using installed SQLite data…"
                thread {
                    try {
                        val parts = clockText.split(":")
                        require(parts.size == 2) { "Use HH:MM" }
                        val hour = parts[0].toInt(); val minute = parts[1].toInt()
                        require(hour in 0..23 && minute in 0..59) { "Invalid time" }
                        val streetFile = File(folder, "streets.sqlite")
                        val graph = if (streetFile.isFile) OfflineStreetGraph.load(streetFile) else null
                        val data = OfflineRouter.read(agencyFiles, LocalDate.parse(dateText), graph)
                        val start = hour * 3600 + minute * 60
                        val result = OfflineRouter.plan(data, a, b, start, start + 18 * 3600)
                        val summary = JourneyUiModel.itinerary(result, data.stops)
                        runOnUiThread {
                            journey.text = summary + "\n\nWalking paths are estimates, not verified sidewalks."
                            status.text = if (graph == null) "Offline • geometric walking estimates"
                                else "Offline • OSM street graph estimates"
                        }
                    } catch (e: Exception) {
                        runOnUiThread { status.text = "Routing error: ${e.message}" }
                    }
                }
            }
        })
        root.addView(Button(this).apply { text = "Back to network downloads"; setOnClickListener { finish() } })
        setContentView(ScrollView(this).apply { addView(root) })
        thread {
            try {
                val indexed = linkedMapOf<String, OfflineRouter.Stop>()
                for (file in agencyFiles) {
                    SQLiteDatabase.openDatabase(file.path, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                        db.rawQuery("SELECT id,name,lat,lon FROM stops", null).use { c ->
                            while (c.moveToNext()) {
                                val id = c.getString(0)
                                indexed[id] = OfflineRouter.Stop(id, c.getString(1) ?: id, c.getDouble(2), c.getDouble(3))
                            }
                        }
                    }
                }
                runOnUiThread {
                    stopIndex = indexed.values.toList()
                    map.stops = stopIndex
                    updateResults()
                    status.text = "${stopIndex.size} installed stops • tap the map or search by name"
                }
            } catch (e: Exception) {
                runOnUiThread { status.text = "Could not read installed stops: ${e.message}" }
            }
        }
    }
}
