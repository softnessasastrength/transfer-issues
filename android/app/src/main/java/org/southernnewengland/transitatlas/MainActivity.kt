package org.southernnewengland.transitatlas

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.database.sqlite.SQLiteDatabase
import android.view.View
import android.webkit.WebView
import android.widget.*
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import kotlin.concurrent.thread

/** Local-first test client. LAN access is explicit, never automatic. */
class MainActivity : Activity() {
    private val names = listOf("cttransit", "hartford", "pvta", "amtrak")
    private lateinit var status: TextView
    private lateinit var host: EditText
    private lateinit var checks: Map<String, CheckBox>
    private val folder get() = File(filesDir, "offline").apply { mkdirs() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val outer = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(22, 30, 22, 22) }
        val title = TextView(this).apply { text = "TRANSIT ATLAS · LOCAL TEST"; textSize = 22f }
        outer.addView(title)
        outer.addView(TextView(this).apply { text = "Mac mini address (same Wi-Fi; no cloud):" })
        host = EditText(this).apply {
            hint = "http://192.168.1.10:8000"
            setSingleLine()
            setText(getPreferences(0).getString("host", ""))
        }
        outer.addView(host)
        outer.addView(TextView(this).apply { text = "Choose networks to install. Only checked agencies download:" })
        checks = names.associateWith { name ->
            CheckBox(this).apply {
                text = name
                isChecked = name in listOf("cttransit", "hartford", "pvta", "amtrak")
                outer.addView(this)
            }
        }
        status = TextView(this).apply { textSize = 14f; setPadding(0, 12, 0, 12) }
        outer.addView(status)
        val download = Button(this).apply { text = "Review selected downloads" }
        val browser = Button(this).apply { text = "Open Mac mini atlas (LAN)" }
        val offline = Button(this).apply { text = "Explore installed offline map" }
        outer.addView(download); outer.addView(browser); outer.addView(offline)
        outer.addView(Button(this).apply { text = "Plan journey offline (Kotlin)"; setOnClickListener { startActivity(Intent(this@MainActivity, OfflinePlannerActivity::class.java)) } })
        setContentView(ScrollView(this).apply { addView(outer) })
        status.text = installedSummary()
        download.setOnClickListener { review() }
        browser.setOnClickListener {
            try {
                val url = baseUrl()
                getPreferences(0).edit().putString("host", url).apply()
                val web = WebView(this)
                web.settings.javaScriptEnabled = true
                web.settings.domStorageEnabled = true
                // LAN WebView loads the existing Python-served explorer and planner.
                setContentView(web)
                web.loadUrl(url)
            } catch (e: Exception) { status.text = e.message }
        }
        offline.setOnClickListener {
            val map = OfflineMap(this, folder)
            val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
            box.addView(Button(this).apply { text = "Back to networks"; setOnClickListener { recreate() } })
            box.addView(TextView(this).apply { text = "Offline GTFS shapes and stops. No street basemap or pedestrian graph."; setPadding(12, 8, 12, 8) })
            box.addView(map, LinearLayout.LayoutParams(-1, 0, 1f))
            setContentView(box)
        }
    }

    private fun baseUrl(): String {
        val raw = host.text.toString().trim().trimEnd('/')
        val parsed = URL(raw)
        require(parsed.protocol == "http" || parsed.protocol == "https") { "Enter a valid HTTP(S) URL" }
        require(parsed.host.isNotBlank() && parsed.userInfo == null && parsed.query == null && parsed.ref == null) { "Enter a server origin only" }
        return raw
    }

    private fun installedSummary(): String = "Installed: " + (names.filter { File(folder, "$it.sqlite").isFile }.joinToString().ifEmpty { "none" })

    private fun review() {
        val chosen = names.filter { checks[it]?.isChecked == true }
        if (chosen.isEmpty()) { status.text = "Select at least one agency."; return }
        val base = try { baseUrl() } catch (e: Exception) { status.text = e.message; return }
        getPreferences(0).edit().putString("host", base).apply()
        status.text = "Checking local catalog…"
        thread {
            try {
                val catalog = JSONObject(URL("$base/api/v1/packs/catalog").readText())
                val packages = catalog.getJSONObject("packages")
                val available = chosen.filter { packages.has(it) }
                val missing = chosen - available.toSet()
                val total = available.sumOf { packages.getJSONObject(it).getLong("bytes") }
                runOnUiThread {
                    val message = "Install: ${available.joinToString()}\nSize: ${total / 1048576.0} MiB\nUnavailable: ${missing.joinToString().ifEmpty { "none" }}\nThis test build downloads only selected available packs, directly from your Mac mini."
                    android.app.AlertDialog.Builder(this)
                        .setTitle("Confirm offline package download")
                        .setMessage(message)
                        .setNegativeButton("Cancel", null)
                        .setPositiveButton("Download") { _, _ -> downloadPacks(base, packages, available) }
                        .show()
                }
            } catch (e: Exception) { runOnUiThread { status.text = "Catalog unavailable: ${e.message}" } }
        }
    }

    private fun downloadPacks(base: String, packages: JSONObject, selected: List<String>) {
        status.text = "Downloading selected packs…"
        thread {
            try {
                for (name in selected) {
                    val info = packages.getJSONObject(name)
                    val expected = info.getString("sha256")
                    val size = info.getLong("bytes")
                    val temp = File(folder, ".$name.download")
                    try {
                        val connection = URL("$base/api/v1/packs/download/$name").openConnection() as HttpURLConnection
                        connection.connectTimeout = 10000
                        connection.readTimeout = 60000
                        try {
                            require(connection.responseCode == 200) { "HTTP ${connection.responseCode} for $name" }
                            val md = MessageDigest.getInstance("SHA-256")
                            var received = 0L
                            connection.inputStream.use { input ->
                                temp.outputStream().use { output ->
                                    val buffer = ByteArray(65536)
                                    while (true) {
                                        val n = input.read(buffer)
                                        if (n < 0) break
                                        output.write(buffer, 0, n)
                                        md.update(buffer, 0, n)
                                        received += n
                                    }
                                }
                            }
                            val actual = md.digest().joinToString("") { "%02x".format(it) }
                            require(received == size && actual.equals(expected, true)) { "Integrity check failed: $name" }
                            SQLiteDatabase.openDatabase(temp.path, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                                db.rawQuery("PRAGMA integrity_check", null).use { c ->
                                    require(c.moveToFirst() && c.getString(0) == "ok") { "SQLite integrity failed: $name" }
                                }
                            }
                            // Replace only after verification; previous pack retained on failure.
                            val target = File(folder, "$name.sqlite")
                            val backup = File(folder, "$name.previous.sqlite")
                            if (target.exists()) { backup.delete(); require(target.renameTo(backup)) }
                            if (!temp.renameTo(target)) {
                                if (backup.exists()) backup.renameTo(target)
                                error("Could not activate $name")
                            }
                        } finally { connection.disconnect() }
                    } finally { temp.delete() }
                }
                runOnUiThread { status.text = "Verified and installed. " + installedSummary() }
            } catch (e: Exception) { runOnUiThread { status.text = "Install stopped: ${e.message}. Existing packs preserved where possible." } }
        }
    }
}

/** Offline geographic preview: plots real GTFS shape points and stops, no remote tiles. */
private class OfflineMap(context: Context, folder: File) : View(context) {
    private val lines = mutableListOf<List<Pair<Float, Float>>>()
    private val stops = mutableListOf<Pair<Float, Float>>()
    private val paint = Paint(3)
    init {
        for (file in folder.listFiles().orEmpty().filter { it.extension == "sqlite" && !it.name.contains("previous") }) {
            try {
                SQLiteDatabase.openDatabase(file.path, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    val shapes = linkedMapOf<String, MutableList<Pair<Float, Float>>>()
                    db.rawQuery("SELECT id, lat, lon FROM shapes ORDER BY id, seq LIMIT 250000", null).use { c ->
                        while (c.moveToNext()) {
                            shapes.getOrPut(c.getString(0)) { mutableListOf() }
                                .add(c.getFloat(2) to c.getFloat(1))
                        }
                    }
                    lines.addAll(shapes.values.filter { it.size > 1 })
                    db.rawQuery("SELECT lon,lat FROM stops LIMIT 10000", null).use { c ->
                        while (c.moveToNext()) stops.add(c.getFloat(0) to c.getFloat(1))
                    }
                }
            } catch (_: Exception) { }
        }
    }
    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawColor(Color.rgb(15, 25, 37))
        val points = lines.flatten() + stops
        if (points.isEmpty()) {
            paint.color = Color.WHITE; paint.textSize = 34f
            canvas.drawText("No usable offline geometry installed", 24f, height / 2f, paint)
            return
        }
        val minX = points.minOf { it.first }; val maxX = points.maxOf { it.first }
        val minY = points.minOf { it.second }; val maxY = points.maxOf { it.second }
        val sx = (width - 36f) / (maxX - minX).coerceAtLeast(0.001f)
        val sy = (height - 36f) / (maxY - minY).coerceAtLeast(0.001f)
        val scale = minOf(sx, sy)
        fun x(v: Float) = 18f + (v - minX) * scale
        fun y(v: Float) = height - 18f - (v - minY) * scale
        paint.style = Paint.Style.STROKE; paint.strokeWidth = 2.2f
        for ((i, line) in lines.withIndex()) {
            paint.color = Color.HSVToColor(floatArrayOf((i * 47 % 360).toFloat(), 0.7f, 0.95f))
            val path = android.graphics.Path()
            line.forEachIndexed { n, pt -> if (n == 0) path.moveTo(x(pt.first), y(pt.second)) else path.lineTo(x(pt.first), y(pt.second)) }
            canvas.drawPath(path, paint)
        }
        paint.style = Paint.Style.FILL; paint.color = Color.WHITE
        for (pt in stops) canvas.drawCircle(x(pt.first), y(pt.second), 1.8f, paint)
    }
}
