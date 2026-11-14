package org.southernnewengland.transitatlas

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.view.MotionEvent
import android.view.View
import kotlin.math.*

/** Offline geographic stop plot. No tile service, internet, or GPS permission. */
internal class StopPickerMap(context: Context) : View(context) {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    var stops: List<OfflineRouter.Stop> = emptyList()
        set(value) { field = value.filter { it.lat.isFinite() && it.lon.isFinite() }; invalidate() }
    var origin: String? = null
        set(value) { field = value; invalidate() }
    var destination: String? = null
        set(value) { field = value; invalidate() }
    var chooseOrigin = true
    var onStopSelected: ((OfflineRouter.Stop) -> Unit)? = null
    private var extent = doubleArrayOf(-73.0, -71.0, 41.0, 43.0)

    private fun bounds() {
        if (stops.isEmpty()) return
        val minLon = stops.minOf { it.lon }; val maxLon = stops.maxOf { it.lon }
        val minLat = stops.minOf { it.lat }; val maxLat = stops.maxOf { it.lat }
        val lonMargin = max(0.01, (maxLon - minLon) * 0.05)
        val latMargin = max(0.01, (maxLat - minLat) * 0.05)
        extent = doubleArrayOf(minLon - lonMargin, maxLon + lonMargin, minLat - latMargin, maxLat + latMargin)
    }

    private fun point(stop: OfflineRouter.Stop): Pair<Float, Float> {
        val x = 18.0 + (stop.lon - extent[0]) / (extent[1] - extent[0]) * max(1, width - 36)
        val y = height - 18.0 - (stop.lat - extent[2]) / (extent[3] - extent[2]) * max(1, height - 36)
        return x.toFloat() to y.toFloat()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawColor(Color.rgb(17, 30, 42))
        bounds()
        paint.style = Paint.Style.FILL
        paint.color = Color.WHITE
        paint.textSize = 29f
        if (stops.isEmpty()) {
            canvas.drawText("Install transit packs to show stops", 20f, height / 2f, paint)
            return
        }
        paint.textSize = 22f
        canvas.drawText("Tap a stop to select ${if (chooseOrigin) "origin" else "destination"}", 15f, 27f, paint)
        for (stop in stops) {
            val (x, y) = point(stop)
            paint.color = when (stop.id) {
                origin -> Color.rgb(52, 211, 153)
                destination -> Color.rgb(251, 191, 36)
                else -> Color.rgb(126, 172, 215)
            }
            canvas.drawCircle(x, y, if (stop.id == origin || stop.id == destination) 9f else 3.5f, paint)
        }
        paint.color = Color.LTGRAY
        paint.textSize = 19f
        canvas.drawText("Geographic stop preview • no street basemap", 15f, height - 7f, paint)
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (event.action != MotionEvent.ACTION_UP) return true
        if (stops.isEmpty()) return true
        val nearest = stops.minByOrNull {
            val (x, y) = point(it)
            hypot(x - event.x, y - event.y)
        } ?: return true
        val (x, y) = point(nearest)
        if (hypot(x - event.x, y - event.y) <= 42f) onStopSelected?.invoke(nearest)
        return true
    }
}
