package com.merabrandpakistan.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.merabrandpakistan.app.ui.AppRoot
import com.merabrandpakistan.app.ui.theme.MbpTheme

class MainActivity : ComponentActivity() {

    private val viewModel: EventViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        val splash = installSplashScreen()
        super.onCreate(savedInstanceState)
        splash.setKeepOnScreenCondition { !viewModel.state.value.ready }
        enableEdgeToEdge()
        setContent {
            MbpTheme {
                AppRoot(viewModel)
            }
        }
    }
}
