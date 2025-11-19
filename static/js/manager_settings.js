/**
 * Manager Settings JavaScript
 * Handles modal interactions and AJAX operations for viscosity rules management
 */

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Global variables
let currentRuleId = null;
let isEditMode = false;

// ============================================================================
// MODAL FUNCTIONS
// ============================================================================

function openModal(ruleId = null) {
    const modal = document.getElementById('ruleModal');
    const modalTitle = document.getElementById('modalTitle');
    const form = document.getElementById('ruleForm');

    // Reset form
    form.reset();
    document.getElementById('ruleId').value = '';
    currentRuleId = null;
    isEditMode = false;

    if (ruleId) {
        // Edit mode - fetch rule data
        isEditMode = true;
        currentRuleId = ruleId;
        modalTitle.textContent = 'Edit Rule';
        loadRuleData(ruleId);
    } else {
        // Add mode
        modalTitle.textContent = 'Add New Rule';
        document.getElementById('isActive').checked = true;
        document.getElementById('displayOrder').value = 999;
    }

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    const modal = document.getElementById('ruleModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    currentRuleId = null;
    isEditMode = false;
}

function loadRuleData(ruleId) {
    // Find the rule card
    const ruleCard = document.querySelector(`[data-rule-id="${ruleId}"]`);
    if (!ruleCard) return;

    // Extract data from the card (this is a simple approach)
    // In a production app, you'd fetch from API
    const nameElement = ruleCard.querySelector('.rule-name');
    const name = nameElement ? nameElement.textContent.trim() : '';

    // For now, we'll need to make an API call to get full data
    // Since we don't have a GET endpoint, we'll use the data attributes or fetch
    // For simplicity, let's extract what we can from the DOM

    // This is simplified - in production you'd want a proper GET endpoint
    document.getElementById('ruleId').value = ruleId;
    // You would populate other fields here from API or data attributes
}

// ============================================================================
// CRUD OPERATIONS
// ============================================================================

async function saveRule(event) {
    event.preventDefault();

    const form = document.getElementById('ruleForm');
    const formData = new FormData(form);

    // Build JSON payload
    const data = {
        name: formData.get('name'),
        min_temperature: formData.get('min_temperature') || null,
        max_temperature: formData.get('max_temperature') || null,
        recommended_viscosity: formData.get('recommended_viscosity'),
        suggestion_text: formData.get('suggestion_text'),
        badge_color: formData.get('badge_color'),
        display_order: parseInt(formData.get('display_order')) || 999,
        is_active: formData.get('is_active') === 'on'
    };

    let url, method;
    if (isEditMode && currentRuleId) {
        url = `/tech/settings/api/viscosity/${currentRuleId}/update/`;
        method = 'POST';  // Using POST for compatibility
    } else {
        url = '/tech/settings/api/viscosity/create/';
        method = 'POST';
    }

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showMessage(result.message, 'success');
            closeModal();
            // Reload page to show changes
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showMessage(result.error || 'Failed to save rule', 'error');
        }
    } catch (error) {
        console.error('Error saving rule:', error);
        showMessage('An error occurred while saving the rule', 'error');
    }
}

async function deleteRule(ruleId, ruleName) {
    if (!confirm(`Are you sure you want to delete the rule "${ruleName}"?\n\nThis action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/tech/settings/api/viscosity/${ruleId}/delete/`, {
            method: 'POST',  // Using POST for compatibility
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        });

        const result = await response.json();

        if (result.success) {
            showMessage(result.message, 'success');
            // Remove card from DOM
            const card = document.querySelector(`[data-rule-id="${ruleId}"]`);
            if (card) {
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    card.remove();
                    // Check if grid is empty
                    const grid = document.getElementById('rulesGrid');
                    if (grid.children.length === 0) {
                        location.reload();
                    }
                }, 300);
            }
        } else {
            showMessage(result.error || 'Failed to delete rule', 'error');
        }
    } catch (error) {
        console.error('Error deleting rule:', error);
        showMessage('An error occurred while deleting the rule', 'error');
    }
}

async function toggleRule(ruleId, isActive) {
    try {
        const response = await fetch(`/tech/settings/api/viscosity/${ruleId}/toggle/`, {
            method: 'POST',  // Using POST for compatibility
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        });

        const result = await response.json();

        if (result.success) {
            showMessage(result.message, 'success');
            // Update card appearance
            const card = document.querySelector(`[data-rule-id="${ruleId}"]`);
            if (card) {
                if (result.is_active) {
                    card.classList.remove('inactive');
                } else {
                    card.classList.add('inactive');
                }
            }
        } else {
            showMessage(result.error || 'Failed to toggle rule', 'error');
            // Revert checkbox
            const checkbox = document.querySelector(`[data-rule-id="${ruleId}"] input[type="checkbox"]`);
            if (checkbox) {
                checkbox.checked = !isActive;
            }
        }
    } catch (error) {
        console.error('Error toggling rule:', error);
        showMessage('An error occurred while toggling the rule', 'error');
        // Revert checkbox
        const checkbox = document.querySelector(`[data-rule-id="${ruleId}"] input[type="checkbox"]`);
        if (checkbox) {
            checkbox.checked = !isActive;
        }
    }
}

function editRule(ruleId) {
    openModal(ruleId);
}

// ============================================================================
// UI FUNCTIONS
// ============================================================================

function showMessage(message, type = 'success') {
    const toast = document.getElementById('messageToast');
    const messageText = document.getElementById('messageText');
    const icon = toast.querySelector('i');

    messageText.textContent = message;

    // Update icon and style based on type
    toast.className = 'message-toast';
    if (type === 'success') {
        toast.classList.add('success');
        icon.className = 'fas fa-check-circle';
    } else if (type === 'error') {
        toast.classList.add('error');
        icon.className = 'fas fa-exclamation-circle';
    }

    toast.style.display = 'flex';

    // Auto-hide after 3 seconds
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Add rule button
    const addRuleBtn = document.getElementById('addRuleBtn');
    if (addRuleBtn) {
        addRuleBtn.addEventListener('click', () => openModal());
    }

    // Form submission
    const ruleForm = document.getElementById('ruleForm');
    if (ruleForm) {
        ruleForm.addEventListener('submit', saveRule);
    }

    // Close modal on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });

    console.log('✅ Manager Settings JavaScript loaded');
});
