package ke.safeundo.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

/** Palette sampled from the My OneApp dark UI. */
object Su {
    val Bg = Color(0xFF121212)
    val Card = Color(0xFF1E1E1E)
    val Raised = Color(0xFF2F2F2F)
    val Outline = Color(0xFF3A4254)
    val Green = Color(0xFF53A24A)
    val GreenSoft = Color(0xFF1D2E1B)
    val Red = Color(0xFFE5484D)
    val Amber = Color(0xFFE8A33D)
    val Blue = Color(0xFF7AA2F7)
    val Text = Color(0xFFF2F2F2)
    val Muted = Color(0xFFA3A7AE)
}

private val Scheme = darkColorScheme(
    primary = Su.Green, onPrimary = Color.White,
    background = Su.Bg, onBackground = Su.Text,
    surface = Su.Card, onSurface = Su.Text,
    surfaceVariant = Su.Raised, onSurfaceVariant = Su.Muted,
    outline = Su.Outline, error = Su.Red,
)

@Composable
fun SafeUndoTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = Scheme, content = content)
}
