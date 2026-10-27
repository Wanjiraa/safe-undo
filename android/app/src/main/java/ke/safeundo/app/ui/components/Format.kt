package ke.safeundo.app.ui.components

import androidx.compose.ui.graphics.Color
import ke.safeundo.app.ui.theme.Su
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

fun kes(x: Double): String = "KSh " + String.format(Locale.US, "%,.0f", x)
fun ksh2(x: Double): String = "Ksh " + String.format(Locale.US, "%,.2f", x)

private fun local(ts: String) = OffsetDateTime.parse(ts).atZoneSameInstant(ZoneId.systemDefault())

private fun ordinal(d: Int) = if (d in 11..13) "th" else when (d % 10) { 1 -> "st"; 2 -> "nd"; 3 -> "rd"; else -> "th" }

/** "21st Oct 2026 | 12:14 pm" */
fun fmtLong(ts: String): String = runCatching {
    val z = local(ts)
    "${z.dayOfMonth}${ordinal(z.dayOfMonth)} " + z.format(DateTimeFormatter.ofPattern("MMM yyyy | h:mm a", Locale.ENGLISH)).replace("AM", "am").replace("PM", "pm")
}.getOrDefault(ts)

/** "21 Oct, 12:14 pm" */
fun fmtShort(ts: String): String = runCatching {
    local(ts).format(DateTimeFormatter.ofPattern("d MMM, h:mm a", Locale.ENGLISH)).replace("AM", "am").replace("PM", "pm")
}.getOrDefault(ts)

fun initials(name: String?): String =
    name.orEmpty().trim().split(" ").filter { it.isNotEmpty() }.take(2).joinToString("") { it.first().uppercase() }

private val avatarPalette = listOf(
    Color(0xFF1B2A5E) to Color(0xFF7AA2F7), Color(0xFF16301F) to Color(0xFF53A24A),
    Color(0xFF2E1A5E) to Color(0xFFA78BFA), Color(0xFF4A1F14) to Color(0xFFE8794D),
    Color(0xFF4A1238) to Color(0xFFD16BB5),
)
fun avatarColors(seed: String): Pair<Color, Color> = avatarPalette[(seed.hashCode() and 0x7fffffff) % avatarPalette.size]

fun riskColor(level: String): Color = when (level) { "Elevated" -> Su.Red; "Moderate" -> Su.Amber; else -> Su.Green }
fun statusColor(status: String): Color = when (status) {
    "completed", "approved" -> Su.Green; "rejected" -> Su.Red; "under_review" -> Su.Amber; else -> Su.Blue
}

/** Accepts 07xx, 7xx, 2547xx; returns 10-digit local form or null. */
fun normalizedPhone(raw: String): String? {
    var d = raw.filter { it.isDigit() }
    if (d.startsWith("254") && d.length == 12) d = "0" + d.substring(3)
    else if (d.length == 9 && (d[0] == '7' || d[0] == '1')) d = "0$d"
    return if (d.length == 10 && d.startsWith("0")) d else null
}
