package com.merabrandpakistan.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.merabrandpakistan.app.EventViewModel
import com.merabrandpakistan.app.UiState
import com.merabrandpakistan.app.data.Exhibitor
import com.merabrandpakistan.app.data.Product
import kotlinx.coroutines.launch

@Composable
fun VisitorApp(viewModel: EventViewModel, state: UiState) {
    val nav = rememberNavController()
    NavHost(navController = nav, startDestination = "home") {
        composable("home") {
            VisitorHome(viewModel, state, onOpenExhibitor = { nav.navigate("exhibitor/$it") })
        }
        composable(
            route = "exhibitor/{id}",
            arguments = listOf(navArgument("id") { type = NavType.StringType }),
        ) { entry ->
            ExhibitorDetailScreen(
                viewModel = viewModel,
                state = state,
                exhibitorId = entry.arguments?.getString("id").orEmpty(),
                onBack = { nav.popBackStack() },
            )
        }
    }
}

private class TabItem(val label: String, val icon: ImageVector)

private val visitorTabs = listOf(
    TabItem("Exhibitors", Icons.Filled.Home),
    TabItem("Products", Icons.Filled.ShoppingCart),
    TabItem("Halls", Icons.Filled.LocationOn),
    TabItem("Meetings", Icons.Filled.DateRange),
    TabItem("Profile", Icons.Filled.Person),
)

@Composable
private fun VisitorHome(viewModel: EventViewModel, state: UiState, onOpenExhibitor: (String) -> Unit) {
    var tab by rememberSaveable { mutableIntStateOf(0) }

    Scaffold(
        topBar = { AppTopBar(visitorTabs[tab].label) },
        bottomBar = {
            NavigationBar {
                visitorTabs.forEachIndexed { index, item ->
                    NavigationBarItem(
                        selected = tab == index,
                        onClick = { tab = index },
                        icon = { Icon(item.icon, contentDescription = null) },
                        label = { Text(item.label, maxLines = 1) },
                    )
                }
            }
        },
    ) { padding ->
        Box(Modifier.padding(padding).fillMaxSize()) {
            when (tab) {
                0 -> ExhibitorsTab(state, onOpenExhibitor)
                1 -> ProductsTab(state, onOpenExhibitor)
                2 -> HallsTab(state, onOpenExhibitor)
                3 -> VisitorMeetingsTab(state)
                else -> ProfileTab(
                    title = state.visitor?.name.orEmpty(),
                    lines = listOfNotNull(
                        state.visitor?.email,
                        state.visitor?.company?.takeIf { it.isNotBlank() },
                        state.visitor?.phone?.takeIf { it.isNotBlank() },
                    ),
                    onLogout = viewModel::logout,
                )
            }
        }
    }
}

@Composable
private fun ExhibitorsTab(state: UiState, onOpen: (String) -> Unit) {
    var query by rememberSaveable { mutableStateOf("") }
    val list = remember(state.exhibitors, query) {
        state.exhibitors.filter {
            it.name.contains(query, true) || it.category.contains(query, true) || it.tagline.contains(query, true)
        }
    }
    Column(Modifier.fillMaxSize()) {
        SearchField(query, { query = it }, "Search exhibitors")
        if (list.isEmpty()) {
            EmptyState("No exhibitors match \"$query\"")
        } else {
            LazyColumn(
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                items(list, key = { it.id }) { exhibitor ->
                    ExhibitorCard(exhibitor, state.locationOf(exhibitor), onClick = { onOpen(exhibitor.id) })
                }
            }
        }
    }
}

@Composable
private fun ExhibitorCard(exhibitor: Exhibitor, location: String, onClick: () -> Unit) {
    ElevatedCard(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(exhibitor.name, style = MaterialTheme.typography.titleMedium)
            Text(
                exhibitor.category,
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
            Text(exhibitor.tagline, style = MaterialTheme.typography.bodyMedium)
            LocationRow(location)
        }
    }
}

@Composable
private fun LocationRow(location: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            Icons.Filled.LocationOn,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.secondary,
            modifier = Modifier.width(18.dp),
        )
        Spacer(Modifier.width(4.dp))
        Text(location, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun ProductsTab(state: UiState, onOpenExhibitor: (String) -> Unit) {
    var query by rememberSaveable { mutableStateOf("") }
    val list = remember(state.products, query) {
        state.products.filter { it.name.contains(query, true) || it.description.contains(query, true) }
    }
    Column(Modifier.fillMaxSize()) {
        SearchField(query, { query = it }, "Search products")
        if (list.isEmpty()) {
            EmptyState("No products match \"$query\"")
        } else {
            LazyColumn(
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                items(list, key = { it.id }) { product ->
                    ProductCard(
                        product = product,
                        exhibitorName = state.exhibitor(product.exhibitorId)?.name.orEmpty(),
                        onClick = { onOpenExhibitor(product.exhibitorId) },
                    )
                }
            }
        }
    }
}

@Composable
fun ProductCard(product: Product, exhibitorName: String, onClick: (() -> Unit)? = null) {
    val content: @Composable () -> Unit = {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(product.name, style = MaterialTheme.typography.titleMedium)
            if (exhibitorName.isNotEmpty()) {
                Text(exhibitorName, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
            }
            Text(product.description, style = MaterialTheme.typography.bodyMedium)
        }
    }
    if (onClick != null) {
        ElevatedCard(onClick = onClick, modifier = Modifier.fillMaxWidth()) { content() }
    } else {
        ElevatedCard(modifier = Modifier.fillMaxWidth()) { content() }
    }
}

@Composable
private fun HallsTab(state: UiState, onOpenExhibitor: (String) -> Unit) {
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        items(state.halls, key = { it.id }) { hall ->
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text(hall.name, style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.primary)
                    Text(hall.description, style = MaterialTheme.typography.bodyMedium)
                    HorizontalDivider(Modifier.padding(vertical = 8.dp))
                    state.exhibitors.filter { it.hallId == hall.id }.forEach { exhibitor ->
                        Row(
                            Modifier
                                .fillMaxWidth()
                                .clickable { onOpenExhibitor(exhibitor.id) }
                                .padding(vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Surface(
                                color = MaterialTheme.colorScheme.secondaryContainer,
                                shape = MaterialTheme.shapes.small,
                            ) {
                                Text(
                                    exhibitor.booth,
                                    style = MaterialTheme.typography.labelLarge,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                )
                            }
                            Spacer(Modifier.width(12.dp))
                            Text(exhibitor.name, style = MaterialTheme.typography.bodyLarge)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun VisitorMeetingsTab(state: UiState) {
    if (state.meetings.isEmpty()) {
        EmptyState("No meeting requests yet.\nOpen an exhibitor and tap \"Request meeting\".")
        return
    }
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        items(state.meetings, key = { it.id }) { meeting ->
            val exhibitor = state.exhibitor(meeting.exhibitorId)
            ElevatedCard(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            exhibitor?.name.orEmpty(),
                            style = MaterialTheme.typography.titleMedium,
                            modifier = Modifier.weight(1f),
                        )
                        StatusChip(meeting.status)
                    }
                    Text(meeting.slot, style = MaterialTheme.typography.bodyMedium)
                    if (exhibitor != null) LocationRow(state.locationOf(exhibitor))
                    if (meeting.message.isNotBlank()) {
                        Text(
                            "\"${meeting.message}\"",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun ProfileTab(title: String, lines: List<String>, onLogout: () -> Unit) {
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(title, style = MaterialTheme.typography.headlineSmall, color = MaterialTheme.colorScheme.primary)
        lines.forEach { Text(it, style = MaterialTheme.typography.bodyLarge) }
        Spacer(Modifier.height(8.dp))
        OutlinedButton(onClick = onLogout, modifier = Modifier.fillMaxWidth()) { Text("Log out") }
    }
}

@Composable
fun ExhibitorDetailScreen(
    viewModel: EventViewModel,
    state: UiState,
    exhibitorId: String,
    onBack: () -> Unit,
) {
    val exhibitor = state.exhibitor(exhibitorId)
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    var showDialog by rememberSaveable { mutableStateOf(false) }

    if (exhibitor == null) {
        EmptyState("Exhibitor not found")
        return
    }

    Scaffold(
        topBar = {
            AppTopBar(exhibitor.name) {
                IconButton(onClick = onBack) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                }
            }
        },
        snackbarHost = { SnackbarHost(snackbar) },
        bottomBar = {
            Surface(tonalElevation = 3.dp) {
                Button(
                    onClick = { showDialog = true },
                    modifier = Modifier
                        .navigationBarsPadding()
                        .fillMaxWidth()
                        .padding(16.dp),
                ) { Text("Request meeting") }
            }
        },
    ) { padding ->
        Column(
            Modifier
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(exhibitor.category, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
            Text(exhibitor.tagline, style = MaterialTheme.typography.titleMedium)
            LocationRow(state.locationOf(exhibitor))
            Text(exhibitor.description, style = MaterialTheme.typography.bodyLarge)
            Text("${exhibitor.email}  ·  ${exhibitor.phone}", style = MaterialTheme.typography.bodySmall)

            Spacer(Modifier.height(8.dp))
            Text("Products", style = MaterialTheme.typography.titleLarge)
            state.products.filter { it.exhibitorId == exhibitor.id }.forEach {
                ProductCard(product = it, exhibitorName = "")
            }
        }
    }

    if (showDialog) {
        MeetingRequestDialog(
            slots = state.slots,
            onDismiss = { showDialog = false },
            onSend = { slot, message ->
                showDialog = false
                viewModel.requestMeeting(exhibitor.id, slot, message) { error ->
                    scope.launch { snackbar.showSnackbar(error ?: "Meeting request sent") }
                }
            },
        )
    }
}

@Composable
private fun MeetingRequestDialog(slots: List<String>, onDismiss: () -> Unit, onSend: (String, String) -> Unit) {
    var slot by rememberSaveable { mutableStateOf(slots.firstOrNull().orEmpty()) }
    var message by rememberSaveable { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Request a meeting") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                slots.forEach { option ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .selectable(selected = slot == option, onClick = { slot = option }, role = Role.RadioButton)
                            .padding(vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(selected = slot == option, onClick = null)
                        Spacer(Modifier.width(8.dp))
                        Text(option)
                    }
                }
                OutlinedTextField(
                    value = message,
                    onValueChange = { message = it },
                    label = { Text("Message (optional)") },
                    modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                )
            }
        },
        confirmButton = {
            TextButton(onClick = { onSend(slot, message.trim()) }, enabled = slot.isNotEmpty()) {
                Text("Send request")
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}
