package com.merabrandpakistan.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val BrandGreen = Color(0xFF01411C)
val BrandGold = Color(0xFFE8B83C)

private val colors = lightColorScheme(
    primary = BrandGreen,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFD5EBDC),
    onPrimaryContainer = Color(0xFF00210E),
    secondary = Color(0xFF5E4A00),
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFFBE8A8),
    onSecondaryContainer = Color(0xFF241A00),
    background = Color.White,
    surface = Color.White,
)

@Composable
fun MbpTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = colors, content = content)
}
