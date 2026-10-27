package ke.safeundo.app.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ke.safeundo.app.ui.theme.Su

@Composable
fun SuScreen(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    Column(
        modifier.fillMaxSize().background(Su.Bg).statusBarsPadding().navigationBarsPadding().imePadding(),
        content = content,
    )
}

@Composable
fun IconCircle(icon: ImageVector, desc: String, onClick: () -> Unit, modifier: Modifier = Modifier, tint: Color = Su.Text, size: Dp = 52.dp) {
    Box(modifier.size(size).clip(CircleShape).background(Su.Raised).clickable(onClick = onClick), contentAlignment = Alignment.Center) {
        Icon(icon, contentDescription = desc, tint = tint)
    }
}

@Composable
fun SuTopBar(title: String, onBack: (() -> Unit)?, trailing: @Composable (BoxScope.() -> Unit)? = null) {
    Box(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp).height(52.dp)) {
        if (onBack != null) IconCircle(Icons.AutoMirrored.Filled.ArrowBack, "Back", onBack, Modifier.align(Alignment.CenterStart))
        Text(title, Modifier.align(Alignment.Center), color = Su.Text, fontSize = 20.sp, fontWeight = FontWeight.Medium)
        trailing?.invoke(this)
    }
}

@Composable
fun PrimaryButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true, loading: Boolean = false) {
    Button(
        onClick = onClick, enabled = enabled && !loading,
        modifier = modifier.fillMaxWidth().height(56.dp), shape = RoundedCornerShape(16.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = Su.Green, contentColor = Color.White,
            disabledContainerColor = Su.Raised, disabledContentColor = Su.Muted,
        ),
    ) {
        if (loading) CircularProgressIndicator(Modifier.size(22.dp), color = Su.Text, strokeWidth = 2.dp)
        else Text(text, fontSize = 17.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
fun SecondaryButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier) {
    OutlinedButton(
        onClick = onClick, modifier = modifier.fillMaxWidth().height(56.dp), shape = RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, Su.Outline), colors = ButtonDefaults.outlinedButtonColors(contentColor = Su.Text),
    ) { Text(text, fontSize = 17.sp, fontWeight = FontWeight.SemiBold) }
}

@Composable
fun SuField(
    label: String, value: String, onChange: (String) -> Unit, placeholder: String,
    modifier: Modifier = Modifier, keyboard: KeyboardType = KeyboardType.Number,
    suffix: String? = null, trailing: @Composable () -> Unit = {}, helper: String? = null, helperColor: Color = Su.Green,
) {
    Column(modifier) {
        Text(label, color = Su.Muted, fontSize = 16.sp, modifier = Modifier.padding(bottom = 8.dp))
        OutlinedTextField(
            value = value, onValueChange = onChange, modifier = Modifier.fillMaxWidth(), singleLine = true,
            placeholder = { Text(placeholder, color = Su.Muted) }, shape = RoundedCornerShape(16.dp),
            keyboardOptions = KeyboardOptions(keyboardType = keyboard),
            trailingIcon = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    trailing()
                    if (suffix != null) Text(suffix, color = Su.Muted, modifier = Modifier.padding(end = 8.dp))
                }
            },
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = Su.Green, unfocusedBorderColor = Su.Outline,
                focusedTextColor = Su.Text, unfocusedTextColor = Su.Text, cursorColor = Su.Green,
            ),
        )
        if (helper != null) Text(helper, color = helperColor, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, modifier = Modifier.padding(top = 6.dp, start = 4.dp))
    }
}

@Composable
fun Avatar(initials: String, bg: Color, fg: Color, size: Dp = 56.dp, textSize: TextUnit = 20.sp) {
    Box(Modifier.size(size).clip(CircleShape).background(bg), contentAlignment = Alignment.Center) {
        Text(initials, color = fg, fontSize = textSize, fontWeight = FontWeight.Bold)
    }
}

@Composable
fun NameAvatar(name: String?, seed: String, size: Dp = 56.dp, textSize: TextUnit = 20.sp) {
    val (bg, fg) = avatarColors(seed)
    Avatar(initials(name), bg, fg, size, textSize)
}

@Composable
fun SegmentedTabs(labels: List<String>, selected: Int, onSelect: (Int) -> Unit, modifier: Modifier = Modifier) {
    Row(modifier.fillMaxWidth().clip(RoundedCornerShape(32.dp)).background(Su.Raised).padding(6.dp)) {
        labels.forEachIndexed { i, l ->
            Box(
                Modifier.weight(1f).height(48.dp).clip(RoundedCornerShape(26.dp))
                    .background(if (i == selected) Su.Green else Color.Transparent).clickable { onSelect(i) },
                contentAlignment = Alignment.Center,
            ) { Text(l, color = Su.Text, fontWeight = FontWeight.SemiBold, fontSize = 15.sp, maxLines = 1, overflow = TextOverflow.Ellipsis) }
        }
    }
}

@Composable
fun Pill(text: String, bg: Color, fg: Color) {
    Text(
        text, color = fg, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
        modifier = Modifier.clip(RoundedCornerShape(50)).background(bg).padding(horizontal = 10.dp, vertical = 4.dp),
    )
}

@Composable
fun SuCard(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    Column(modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(Su.Card).padding(16.dp), content = content)
}

@Composable
fun SimulatedBanner(text: String = "Simulated feature. Not connected to the live My OneApp or M-PESA.") {
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).background(Su.GreenSoft).padding(horizontal = 12.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Icon(Icons.Outlined.Info, null, tint = Su.Green, modifier = Modifier.size(16.dp))
        Text(text, color = Color(0xFFB9E0B4), fontSize = 12.sp)
    }
}

@Composable
fun SectionTitle(text: String, modifier: Modifier = Modifier) {
    Text(text, color = Su.Text, fontSize = 20.sp, fontWeight = FontWeight.Bold, modifier = modifier.padding(vertical = 8.dp))
}

@Composable
fun OutlinedTag(text: String, color: Color) {
    Text(
        text, color = color, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
        modifier = Modifier.clip(RoundedCornerShape(50)).border(1.dp, color, RoundedCornerShape(50)).padding(horizontal = 10.dp, vertical = 3.dp),
    )
}
