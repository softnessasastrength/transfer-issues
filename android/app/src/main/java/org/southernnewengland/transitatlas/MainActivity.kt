package org.southernnewengland.transitatlas

import android.app.Activity
import android.os.Bundle
import android.database.sqlite.SQLiteDatabase
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Button
import android.widget.ScrollView
import java.io.File
import java.security.MessageDigest

/** Offline-first starter: no server connection is required to open this screen. */
class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(36, 48, 36, 36)
        }
        val title = TextView(this).apply { text = "Southern New England Transit Atlas"; textSize = 23f }
        val status = TextView(this).apply { textSize = 16f; setPadding(0, 24, 0, 24) }
        val explore = Button(this).apply { text = "Explore offline transit data" }
        val refresh = Button(this).apply { text = "Check installed data pack" }
        layout.addView(title)
        layout.addView(status)
        layout.addView(explore)
        layout.addView(refresh)
        setContentView(ScrollView(this).apply { addView(layout) })
        fun checkPack(): Boolean {
            val pack = File(filesDir, "offline/atlas.sqlite")
            if (!pack.isFile) {
                status.text = "No offline data pack installed. See android/README.md to install one via adb.\nNo internet connection is needed to open this app."
                return false
            }
            return try {
                val db = SQLiteDatabase.openDatabase(pack.path, null, SQLiteDatabase.OPEN_READONLY)
                val routes = db.rawQuery("SELECT COUNT(*) FROM routes", null).use { if (it.moveToFirst()) it.getInt(0) else 0 }
                val stops = db.rawQuery("SELECT COUNT(*) FROM stops", null).use { if (it.moveToFirst()) it.getInt(0) else 0 }
                db.close()
                status.text = "Offline pack loaded: $routes routes and $stops stops.\nRouting and offline maps are not yet implemented."
                true
            } catch (e: Exception) {
                status.text = "Offline pack could not be opened: ${e.message}"
                false
            }
        }
        refresh.setOnClickListener { checkPack() }
        explore.setOnClickListener {
            if (checkPack()) {
                val db = SQLiteDatabase.openDatabase(File(filesDir, "offline/atlas.sqlite").path, null, SQLiteDatabase.OPEN_READONLY)
                val items = mutableListOf<String>()
                db.rawQuery("SELECT COALESCE(short,''),COALESCE(name,''),feed FROM routes ORDER BY feed,short LIMIT 100", null).use { cursor ->
                    while (cursor.moveToNext()) items.add("${cursor.getString(0)} · ${cursor.getString(1)} (${cursor.getString(2)})")
                }
                db.close()
                status.text = "First 100 locally stored routes:\n\n" + items.joinToString("\n")
            }
        }
        checkPack()
    }
}
