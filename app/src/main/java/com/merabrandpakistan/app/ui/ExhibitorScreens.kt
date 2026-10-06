package com.merabrandpakistan.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import com.merabrandpakistan.app.EventViewModel
import com.merabrandpakistan.app.UiState
import com.merabrandpakistan.app.data.MeetingRequest
import com.merabrandpakistan.app.data.MeetingStatus

private class ExhibitorTab(val label: String, val icon: ImageVector)

private val exhibitorTabs = listOf(
    ExhibitorTab("Dashboard", Icons.Filled.Home),
    ExhibitorTab("Requests", Icons.Filled.Notifications),
    ExhibitorTab("Products", Icons.Filled.ShoppingCart),
    ExhibitorTab("Profile", Icons.Filled.Person),
)

@Composable
fun ExhibitorApp(viewModel: EventViewModel, state: UiState) {
    var tab by rememberSaveable { mutableIntStateOf(0) }
    val exhibitor = state.exhibitor ?: return

    Scaffold(
        topBar = { AppTopBar(exhibitorTabs[tab].label) },
        bottomBar = {
            NavigationBar {
                exhibitorTabs.forEachIndexed { index, item ->
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
                0 -> DashboardTab(state, onSeeRequests = { tab = 1 })
                1 -> RequestsTab(state, onRespond = viewModel::respond)
                2 -> ExhibitorProductsTab(state)
                else -> ProfileTab(
                    title = exhibitor.name,
                    lines = listOf(
                        "Exhibitor ID: ${exhibitor.id}",
                        state.locationOf(exhibitor),
                        exhibitor.email,
                        exhibitor.phone,
                    ),
                    onLogout = viewModel::logout,
                )
            }
        }
    }
}

@Composable
private fun DashboardTab(state: UiState, onSeeRequests: () -> Unit) {
    val exhibitor = state.exhibitor ?: return
    val pending = state.meetings.count { it.status == MeetingStatus.PENDING }
    val accepted = state.meetings.filter { it.status == MeetingStatus.ACCEPTED }
    val declined = state.meetings.count { it.status == MeetingStatus.DECLINED }
    val upcoming = accepted.sortedBy { state.slots.indexOf(it.slot) }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Column {
            Text("Welcome,", style = MaterialTheme.typography.bodyMedium)
            Text(exhibitor.name, style = MaterialTheme.typography.headlineSmall, color = MaterialTheme.colorScheme.primary)
            Text(state.locationOf(exhibitor), style = MaterialTheme.typography.bodyMedium)
        }

        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            StatCard("Pending", pending, Modifier.weight(1f))
            StatCard("Accepted", accepted.size, Modifier.weight(1f))
            StatCard("Declined", declined, Modifier.weight(1f))
        }

        if (pending > 0) {
            Button(onClick = onSeeRequests, modifier = Modifier.fillMaxWidth()) {
                Text("Review $pending pending request${if (pending == 1) "" else "s"}")
            }
        }

        Text("Upcoming meetings", style = MaterialTheme.typography.titleLarge)
        if (upcoming.isEmpty()) {
            Text(
                "No accepted meetings yet.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        } else {
            upcoming.forEach { meeting ->
                ElevatedCard(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(meeting.slot, style = MaterialTheme.typography.titleMedium)
                        Text(meeting.visitorName, style = MaterialTheme.typography.bodyLarge)
                        if (meeting.visitorCompany.isNotBlank()) {
                            Text(meeting.visitorCompany, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StatCard(label: String, value: Int, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
    ) {
        Column(Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(value.toString(), style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.primary)
            Text(label, style = MaterialTheme.typography.labelLarge)
        }
    }
}

@Composable
private fun RequestsTab(state: UiState, onRespond: (String, MeetingStatus) -> Unit) {
    // null = show all
    var filter by rememberSaveable { mutableStateOf("ALL") }
    val shown = state.meetings.filter { filter == "ALL" || it.status.name == filter }

    Column(Modifier.fillMaxSize()) {
        Row(
            Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            listOf("ALL" to "All", "PENDING" to "Pending", "ACCEPTED" to "Accepted", "DECLINED" to "Declined")
                .forEach { (key, label) ->
                    FilterChip(selected = filter == key, onClick = { filter = key }, label = { Text(label) })
                }
        }
        if (shown.isEmpty()) {
            EmptyState("No meeting requests here.")
        } else {
            LazyColumn(
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                items(shown, key = { it.id }) { meeting ->
                    RequestCard(meeting, onRespond)
                }
            }
        }
    }
}

@Composable
private fun RequestCard(meeting: MeetingRequest, onRespond: (String, MeetingStatus) -> Unit) {
    ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(meeting.visitorName, style = MaterialTheme.typography.titleMedium)
                    if (meeting.visitorCompany.isNotBlank()) {
                        Text(meeting.visitorCompany, style = MaterialTheme.typography.bodySmall)
                    }
                }
                StatusChip(meeting.status)
            }
            Text(meeting.slot, style = MaterialTheme.typography.bodyLarge)
            if (meeting.message.isNotBlank()) {
                Text(
                    "\"${meeting.message}\"",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            if (meeting.status == MeetingStatus.PENDING) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
                    Button(onClick = { onRespond(meeting.id, MeetingStatus.ACCEPTED) }) { Text("Accept") }
                    OutlinedButton(onClick = { onRespond(meeting.id, MeetingStatus.DECLINED) }) { Text("Decline") }
                }
            }
        }
    }
}

@Composable
private fun ExhibitorProductsTab(state: UiState) {
    val exhibitor = state.exhibitor ?: return
    val products = state.products.filter { it.exhibitorId == exhibitor.id }
    if (products.isEmpty()) {
        EmptyState("No products listed yet.")
        return
    }
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        items(products, key = { it.id }) { ProductCard(product = it, exhibitorName = "") }
    }
}
