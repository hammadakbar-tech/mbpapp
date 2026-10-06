package com.merabrandpakistan.app.ui

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.merabrandpakistan.app.EventViewModel
import com.merabrandpakistan.app.data.Session

/** Shows the login flow, the exhibitor app or the visitor app depending on who is signed in. */
@Composable
fun AppRoot(viewModel: EventViewModel) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        if (state.ready) {
            when (state.session) {
                Session.LoggedOut -> AuthFlow(viewModel)
                is Session.ExhibitorSession -> ExhibitorApp(viewModel, state)
                is Session.VisitorSession -> VisitorApp(viewModel, state)
            }
        }
    }
}

@Composable
private fun AuthFlow(viewModel: EventViewModel) {
    val nav = rememberNavController()
    NavHost(navController = nav, startDestination = "welcome") {
        composable("welcome") {
            WelcomeScreen(
                onExhibitor = { nav.navigate("exhibitor_login") },
                onVisitor = { nav.navigate("visitor_auth") },
            )
        }
        composable("exhibitor_login") {
            ExhibitorLoginScreen(viewModel, onBack = { nav.popBackStack() })
        }
        composable("visitor_auth") {
            VisitorAuthScreen(viewModel, onBack = { nav.popBackStack() })
        }
    }
}
