package com.merabrandpakistan.app

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.merabrandpakistan.app.data.DemoRepository
import com.merabrandpakistan.app.data.EventRepository
import com.merabrandpakistan.app.data.Exhibitor
import com.merabrandpakistan.app.data.Hall
import com.merabrandpakistan.app.data.MeetingRequest
import com.merabrandpakistan.app.data.MeetingStatus
import com.merabrandpakistan.app.data.Product
import com.merabrandpakistan.app.data.Session
import com.merabrandpakistan.app.data.Visitor
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class UiState(
    val ready: Boolean = false,
    val halls: List<Hall> = emptyList(),
    val exhibitors: List<Exhibitor> = emptyList(),
    val products: List<Product> = emptyList(),
    val slots: List<String> = emptyList(),
    val session: Session = Session.LoggedOut,
    val visitor: Visitor? = null,
    val exhibitor: Exhibitor? = null,
    val meetings: List<MeetingRequest> = emptyList(),
) {
    fun hall(id: String): Hall? = halls.firstOrNull { it.id == id }
    fun exhibitor(id: String): Exhibitor? = exhibitors.firstOrNull { it.id == id }

    /** e.g. "Hall 2 · Booth C-09" */
    fun locationOf(e: Exhibitor): String = "${hall(e.hallId)?.name ?: "Hall"} · Booth ${e.booth}"
}

class EventViewModel(app: Application) : AndroidViewModel(app) {

    // Swap this for a network-backed implementation to connect the real server.
    private val repo: EventRepository = DemoRepository(app.applicationContext)

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            _state.update {
                it.copy(
                    halls = repo.halls(),
                    exhibitors = repo.exhibitors(),
                    products = repo.products(),
                    slots = repo.meetingSlots(),
                )
            }
            val saved = repo.savedSession()
            val valid = when (saved) {
                Session.LoggedOut -> true
                is Session.ExhibitorSession -> _state.value.exhibitor(saved.exhibitorId) != null
                is Session.VisitorSession -> repo.visitor(saved.visitorId) != null
            }
            enter(if (valid) saved else Session.LoggedOut)
        }
    }

    fun loginExhibitor(id: String, pin: String, onResult: (String?) -> Unit) {
        viewModelScope.launch {
            val result = repo.loginExhibitor(id, pin)
            if (result.isSuccess) {
                enter(Session.ExhibitorSession(result.getOrThrow().id))
                onResult(null)
            } else {
                onResult(result.exceptionOrNull()?.message ?: "Login failed")
            }
        }
    }

    fun loginVisitor(email: String, password: String, onResult: (String?) -> Unit) {
        viewModelScope.launch {
            val result = repo.loginVisitor(email, password)
            if (result.isSuccess) {
                enter(Session.VisitorSession(result.getOrThrow().id))
                onResult(null)
            } else {
                onResult(result.exceptionOrNull()?.message ?: "Login failed")
            }
        }
    }

    fun registerVisitor(
        name: String,
        email: String,
        company: String,
        phone: String,
        password: String,
        onResult: (String?) -> Unit,
    ) {
        viewModelScope.launch {
            val result = repo.registerVisitor(name, email, company, phone, password)
            if (result.isSuccess) {
                enter(Session.VisitorSession(result.getOrThrow().id))
                onResult(null)
            } else {
                onResult(result.exceptionOrNull()?.message ?: "Registration failed")
            }
        }
    }

    fun logout() {
        viewModelScope.launch { enter(Session.LoggedOut) }
    }

    fun requestMeeting(exhibitorId: String, slot: String, message: String, onResult: (String?) -> Unit) {
        viewModelScope.launch {
            val visitor = _state.value.visitor
            if (visitor == null) {
                onResult("Please sign in again")
                return@launch
            }
            val result = repo.requestMeeting(visitor, exhibitorId, slot, message)
            if (result.isSuccess) {
                refreshMeetings()
                onResult(null)
            } else {
                onResult(result.exceptionOrNull()?.message ?: "Could not send request")
            }
        }
    }

    fun respond(meetingId: String, status: MeetingStatus) {
        viewModelScope.launch {
            repo.respondToMeeting(meetingId, status)
            refreshMeetings()
        }
    }

    private suspend fun enter(session: Session) {
        repo.saveSession(session)
        val visitor = (session as? Session.VisitorSession)?.let { repo.visitor(it.visitorId) }
        val exhibitor = (session as? Session.ExhibitorSession)?.let { _state.value.exhibitor(it.exhibitorId) }
        val meetings = when (session) {
            Session.LoggedOut -> emptyList()
            is Session.ExhibitorSession -> repo.meetingsForExhibitor(session.exhibitorId)
            is Session.VisitorSession -> repo.meetingsForVisitor(session.visitorId)
        }
        _state.update {
            it.copy(
                ready = true,
                session = session,
                visitor = visitor,
                exhibitor = exhibitor,
                meetings = meetings,
            )
        }
    }

    private suspend fun refreshMeetings() {
        val meetings = when (val s = _state.value.session) {
            Session.LoggedOut -> emptyList()
            is Session.ExhibitorSession -> repo.meetingsForExhibitor(s.exhibitorId)
            is Session.VisitorSession -> repo.meetingsForVisitor(s.visitorId)
        }
        _state.update { it.copy(meetings = meetings) }
    }
}
