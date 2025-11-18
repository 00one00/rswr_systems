/**
 * Multi-Break Repair Entry JavaScript
 * Handles state management, modal interactions, pricing preview, and form submission
 */

// State management
let breaks = [];
let editingIndex = null;

// Initialize datetime field with current time
document.addEventListener('DOMContentLoaded', function() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');

    const dateTimeString = `${year}-${month}-${day}T${hours}:${minutes}`;
    document.getElementById('repair_date').value = dateTimeString;

    // Set up pricing preview listeners
    setupPricingPreview();

    // Restore from localStorage if available
    restoreFromLocalStorage();
});

// Helper function to generate UUID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Get CSRF token for AJAX requests
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

// Pricing Preview Setup
function setupPricingPreview() {
    const customerSelect = document.getElementById('customer');
    const unitInput = document.getElementById('unit_number');

    customerSelect.addEventListener('change', updatePricingPreview);
    unitInput.addEventListener('input', debounce(updatePricingPreview, 500));
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function updatePricingPreview() {
    const customerId = document.getElementById('customer').value;
    const unitNumber = document.getElementById('unit_number').value;
    const breaksCount = breaks.length;

    if (!customerId || !unitNumber || breaksCount === 0) {
        document.getElementById('pricingPreview').classList.add('hidden');
        return;
    }

    // Fetch pricing from backend
    fetch(`/tech/api/batch-pricing/?customer_id=${customerId}&unit_number=${encodeURIComponent(unitNumber)}&breaks_count=${breaksCount}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Pricing error:', data.error);
                return;
            }

            displayPricingPreview(data);
        })
        .catch(error => {
            console.error('Error fetching pricing:', error);
        });
}

function displayPricingPreview(pricingData) {
    const previewDiv = document.getElementById('pricingPreview');
    const detailsDiv = document.getElementById('pricingDetails');

    let html = `
        <div class="mb-2">
            <span class="font-semibold">Customer:</span> ${pricingData.customer_name}
            ${pricingData.uses_custom_pricing ? '<span class="ml-2 px-2 py-0.5 bg-purple-100 text-purple-800 text-xs rounded">Custom Pricing</span>' : ''}
        </div>
        <div class="mb-2">
            <span class="font-semibold">Unit ${pricingData.unit_number}:</span> ${pricingData.total_breaks} break(s) |
            <span class="font-semibold text-blue-900">${pricingData.price_range}</span>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3">
    `;

    pricingData.breakdown.forEach(item => {
        html += `
            <div class="text-xs bg-white rounded px-2 py-1 border border-blue-200">
                <div class="font-semibold">Break ${item.break_number}</div>
                <div class="text-gray-600">${item.price_formatted}</div>
                <div class="text-gray-500">(Repair #${item.repair_tier})</div>
            </div>
        `;
    });

    html += `
        </div>
        <div class="mt-3 text-base font-bold">
            Total: ${pricingData.total_cost_formatted}
        </div>
    `;

    detailsDiv.innerHTML = html;
    previewDiv.classList.remove('hidden');

    // Update total cost display
    document.getElementById('totalCost').textContent = pricingData.total_cost_formatted;
}

// Modal Functions
function showModal() {
    const modal = document.getElementById('breakModal');
    modal.classList.add('active');

    const title = editingIndex !== null ? 'Edit Break' : 'Add Break';
    document.getElementById('modalTitle').textContent = title;
}

function hideModal() {
    const modal = document.getElementById('breakModal');
    modal.classList.remove('active');
}

function clearModal() {
    document.getElementById('modal_damage_type').value = '';
    document.getElementById('modal_drilled_before_repair').checked = false;
    document.getElementById('modal_windshield_temperature').value = '';
    document.getElementById('modal_resin_viscosity').value = '';
    document.getElementById('modal_photo_before').value = '';
    document.getElementById('modal_photo_after').value = '';
    document.getElementById('modal_notes').value = '';
    document.getElementById('preview_before').innerHTML = '';
    document.getElementById('preview_after').innerHTML = '';

    // Clear manager override fields if they exist
    const costOverride = document.getElementById('modal_cost_override');
    const overrideReason = document.getElementById('modal_override_reason');
    if (costOverride) costOverride.value = '';
    if (overrideReason) overrideReason.value = '';

    // Hide required indicator for override reason
    const reasonRequired = document.getElementById('override_reason_required');
    if (reasonRequired) reasonRequired.style.display = 'none';
}

// Add Break Button
document.getElementById('addBreakBtn').addEventListener('click', () => {
    console.log('Add Break clicked');
    editingIndex = null;
    console.log('editingIndex set to:', editingIndex);
    clearModal();
    showModal();
});

// Close Modal Buttons
document.getElementById('closeModalBtn').addEventListener('click', hideModal);
document.getElementById('cancelBreakBtn').addEventListener('click', hideModal);

// Click outside modal to close
document.getElementById('breakModal').addEventListener('click', (e) => {
    if (e.target.id === 'breakModal') {
        hideModal();
    }
});

// Save Break Button
document.getElementById('saveBreakBtn').addEventListener('click', () => {
    console.log('Save Break clicked - editingIndex:', editingIndex);

    const damageType = document.getElementById('modal_damage_type').value;
    const drilledBefore = document.getElementById('modal_drilled_before_repair').checked;
    const windshieldTemp = document.getElementById('modal_windshield_temperature').value;
    const resinViscosity = document.getElementById('modal_resin_viscosity').value;
    const photoBefore = document.getElementById('modal_photo_before').files[0];
    const photoAfter = document.getElementById('modal_photo_after').files[0];
    const notes = document.getElementById('modal_notes').value;

    // Get manager override fields if they exist
    const costOverrideEl = document.getElementById('modal_cost_override');
    const overrideReasonEl = document.getElementById('modal_override_reason');
    const costOverride = costOverrideEl ? costOverrideEl.value : '';
    const overrideReason = overrideReasonEl ? overrideReasonEl.value : '';

    console.log('Damage type:', damageType);

    // Validation
    if (!damageType) {
        alert('Please select a damage type');
        return;
    }

    // Validate override reason if override price is set
    if (costOverride && !overrideReason) {
        alert('Override reason is required when setting a custom price');
        return;
    }

    // Photos are optional - can be added later
    // Updated: November 9, 2025 - Removed photo validation

    const breakData = {
        id: editingIndex !== null ? breaks[editingIndex].id : generateUUID(),
        damage_type: damageType,
        drilled_before_repair: drilledBefore,
        windshield_temperature: windshieldTemp,
        resin_viscosity: resinViscosity,
        photo_before: photoBefore || (editingIndex !== null ? breaks[editingIndex].photo_before : null),
        photo_after: photoAfter || (editingIndex !== null ? breaks[editingIndex].photo_after : null),
        notes: notes,
        cost_override: costOverride,
        override_reason: overrideReason
    };

    // Add or update
    if (editingIndex !== null) {
        console.log('Updating existing break at index:', editingIndex);
        breaks[editingIndex] = breakData;
    } else {
        console.log('Adding new break');
        breaks.push(breakData);
    }

    console.log('Total breaks after save:', breaks.length);

    renderBreaksList();
    hideModal();
    clearModal();
    editingIndex = null;  // Reset editing index after save
    console.log('editingIndex reset to:', editingIndex);
    saveToLocalStorage();
    updatePricingPreview();
});

// Photo Preview Handlers
document.getElementById('modal_photo_before').addEventListener('change', (e) => {
    const file = e.target.files[0];
    const preview = document.getElementById('preview_before');

    if (file) {
        // Validate file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/heic', 'image/heif'];
        if (!validTypes.includes(file.type.toLowerCase())) {
            preview.innerHTML = `<div class="mt-2 p-2 bg-red-100 border border-red-300 rounded text-red-700 text-sm">
                <i class="fas fa-exclamation-triangle mr-1"></i> Invalid file type. Please upload JPG, PNG, WebP, or HEIC images.
            </div>`;
            e.target.value = ''; // Clear the input
            return;
        }

        // Validate file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            preview.innerHTML = `<div class="mt-2 p-2 bg-red-100 border border-red-300 rounded text-red-700 text-sm">
                <i class="fas fa-exclamation-triangle mr-1"></i> File too large. Maximum size is 5MB.
            </div>`;
            e.target.value = ''; // Clear the input
            return;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
            preview.innerHTML = `<img src="${event.target.result}" alt="Preview" class="mt-2 max-w-full h-32 rounded border border-gray-300">`;
        };
        reader.onerror = () => {
            preview.innerHTML = `<div class="mt-2 p-2 bg-red-100 border border-red-300 rounded text-red-700 text-sm">
                <i class="fas fa-exclamation-triangle mr-1"></i> Error loading photo preview.
            </div>`;
        };
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = '';
    }
});

document.getElementById('modal_photo_after').addEventListener('change', (e) => {
    const file = e.target.files[0];
    const preview = document.getElementById('preview_after');

    if (file) {
        // Validate file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/heic', 'image/heif'];
        if (!validTypes.includes(file.type.toLowerCase())) {
            preview.innerHTML = `<div class="mt-2 p-2 bg-red-100 border border-red-300 rounded text-red-700 text-sm">
                <i class="fas fa-exclamation-triangle mr-1"></i> Invalid file type. Please upload JPG, PNG, WebP, or HEIC images.
            </div>`;
            e.target.value = ''; // Clear the input
            return;
        }

        // Validate file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            preview.innerHTML = `<div class="mt-2 p-2 bg-red-100 border border-red-300 rounded text-red-700 text-sm">
                <i class="fas fa-exclamation-triangle mr-1"></i> File too large. Maximum size is 5MB.
            </div>`;
            e.target.value = ''; // Clear the input
            return;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
            preview.innerHTML = `<img src="${event.target.result}" alt="Preview" class="mt-2 max-w-full h-32 rounded border border-gray-300">`;
        };
        reader.onerror = () => {
            preview.innerHTML = `<div class="mt-2 p-2 bg-red-100 border border-red-300 rounded text-red-700 text-sm">
                <i class="fas fa-exclamation-triangle mr-1"></i> Error loading photo preview.
            </div>`;
        };
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = '';
    }
});

// Edit Break Function
window.editBreak = function(index) {
    editingIndex = index;
    const breakData = breaks[index];

    document.getElementById('modal_damage_type').value = breakData.damage_type;
    document.getElementById('modal_drilled_before_repair').checked = breakData.drilled_before_repair || false;
    document.getElementById('modal_windshield_temperature').value = breakData.windshield_temperature || '';
    document.getElementById('modal_resin_viscosity').value = breakData.resin_viscosity || '';
    document.getElementById('modal_notes').value = breakData.notes;

    // Populate manager override fields if they exist
    const costOverrideEl = document.getElementById('modal_cost_override');
    const overrideReasonEl = document.getElementById('modal_override_reason');
    if (costOverrideEl) costOverrideEl.value = breakData.cost_override || '';
    if (overrideReasonEl) overrideReasonEl.value = breakData.override_reason || '';

    // Show existing photos if available
    if (breakData.photo_before) {
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('preview_before').innerHTML =
                `<img src="${e.target.result}" alt="Preview" class="mt-2 max-w-full h-32 rounded border border-gray-300">`;
        };
        reader.readAsDataURL(breakData.photo_before);
    }

    if (breakData.photo_after) {
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('preview_after').innerHTML =
                `<img src="${e.target.result}" alt="Preview" class="mt-2 max-w-full h-32 rounded border border-gray-300">`;
        };
        reader.readAsDataURL(breakData.photo_after);
    }

    showModal();
};

// Delete Break Function
window.deleteBreak = function(index) {
    if (confirm(`Are you sure you want to delete Break ${index + 1}?`)) {
        breaks.splice(index, 1);
        renderBreaksList();
        saveToLocalStorage();
        updatePricingPreview();
    }
};

// Render Breaks List
function renderBreaksList() {
    const container = document.getElementById('breaksList');
    const emptyState = document.getElementById('emptyState');
    const submitSection = document.getElementById('submitSection');

    console.log('renderBreaksList - breaks.length:', breaks.length);
    console.log('emptyState element:', emptyState);
    console.log('submitSection element:', submitSection);

    if (!emptyState || !submitSection || !container) {
        console.error('Required elements not found!');
        return;
    }

    if (breaks.length === 0) {
        emptyState.classList.remove('hidden');
        submitSection.classList.add('hidden');
    } else {
        emptyState.classList.add('hidden');
        submitSection.classList.remove('hidden');

        // Clear only the break cards, not the emptyState element
        const breakCards = container.querySelectorAll('.break-card');
        breakCards.forEach(card => card.remove());

        // Add all breaks
        breaks.forEach((breakData, index) => {
            const card = createBreakCard(breakData, index);
            container.appendChild(card);
        });
    }

    // Update counters
    document.getElementById('breakCountBadge').textContent = `${breaks.length} break${breaks.length !== 1 ? 's' : ''} added`;
    document.getElementById('submitBreakCount').textContent = breaks.length;
    document.getElementById('breaks_count').value = breaks.length;
}

function createBreakCard(breakData, index) {
    const card = document.createElement('div');
    card.className = 'break-card bg-white border border-gray-300 rounded-lg p-3 hover:shadow-md transition-all';

    const damageTypeLabel = document.querySelector(`#modal_damage_type option[value="${breakData.damage_type}"]`)?.text || breakData.damage_type;

    // Build technical details display
    let technicalDetails = [];
    if (breakData.drilled_before_repair) {
        technicalDetails.push('<span class="inline-flex items-center text-xs text-blue-600"><i class="fas fa-check-circle mr-1"></i>Pre-drilled</span>');
    }
    if (breakData.windshield_temperature) {
        technicalDetails.push(`<span class="text-xs text-gray-600"><i class="fas fa-thermometer-half mr-1"></i>${breakData.windshield_temperature}°F</span>`);
    }
    if (breakData.resin_viscosity) {
        technicalDetails.push(`<span class="text-xs text-gray-600"><i class="fas fa-tint mr-1"></i>${breakData.resin_viscosity}</span>`);
    }
    if (breakData.cost_override) {
        technicalDetails.push(`<span class="inline-flex items-center text-xs text-purple-600 font-semibold"><i class="fas fa-dollar-sign mr-1"></i>Override: $${breakData.cost_override}</span>`);
    }

    const technicalDetailsHTML = technicalDetails.length > 0 ?
        `<div class="flex flex-wrap gap-2 mt-2 mb-2">${technicalDetails.join('')}</div>` : '';

    // Check for missing photos and create warning badges
    let photoWarnings = [];
    if (!breakData.photo_before && !breakData.photo_after) {
        photoWarnings.push('<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded bg-orange-100 text-orange-800"><i class="fas fa-exclamation-triangle mr-1"></i>Missing both photos</span>');
    } else if (!breakData.photo_before) {
        photoWarnings.push('<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded bg-orange-100 text-orange-800"><i class="fas fa-exclamation-triangle mr-1"></i>Missing before photo</span>');
    } else if (!breakData.photo_after) {
        photoWarnings.push('<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded bg-orange-100 text-orange-800"><i class="fas fa-exclamation-triangle mr-1"></i>Missing after photo</span>');
    }
    const photoWarningsHTML = photoWarnings.length > 0 ?
        `<div class="flex flex-wrap gap-2 mb-2">${photoWarnings.join('')}</div>` : '';

    card.innerHTML = `
        ${photoWarningsHTML}
        <div class="flex justify-between items-start mb-3">
            <div class="flex items-center">
                <span class="inline-flex items-center justify-center h-8 w-8 rounded-full bg-green-100 text-green-800 font-semibold text-sm mr-3">
                    ${index + 1}
                </span>
                <div>
                    <h3 class="font-semibold text-gray-900">Break ${index + 1}</h3>
                    <p class="text-sm text-gray-600">${damageTypeLabel}</p>
                </div>
            </div>
            <div class="flex gap-2">
                <button type="button" onclick="editBreak(${index})" class="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors">
                    Edit
                </button>
                <button type="button" onclick="deleteBreak(${index})" class="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors">
                    Delete
                </button>
            </div>
        </div>
        ${technicalDetailsHTML}
        <div class="grid grid-cols-2 gap-3 mt-3">
            <div>
                <p class="text-xs font-medium text-gray-700 mb-1.5">Photo Before:</p>
                <div class="aspect-[4/3] bg-gray-100 rounded border border-gray-300 overflow-hidden flex items-center justify-center">
                    ${breakData.photo_before ? (() => {
                        try {
                            const url = URL.createObjectURL(breakData.photo_before);
                            return `<img src="${url}" alt="Before photo" class="h-full w-full object-cover" onerror="this.parentElement.innerHTML='<span class=\\'text-red-500 text-xs\\'>Failed to load</span>'">`;
                        } catch(e) {
                            console.error('Error creating preview for photo_before:', e);
                            return '<span class="text-red-500 text-xs">Preview error</span>';
                        }
                    })() : '<span class="text-gray-400 text-xs">No photo</span>'}
                </div>
            </div>
            <div>
                <p class="text-xs font-medium text-gray-700 mb-1.5">Photo After:</p>
                <div class="aspect-[4/3] bg-gray-100 rounded border border-gray-300 overflow-hidden flex items-center justify-center">
                    ${breakData.photo_after ? (() => {
                        try {
                            const url = URL.createObjectURL(breakData.photo_after);
                            return `<img src="${url}" alt="After photo" class="h-full w-full object-cover" onerror="this.parentElement.innerHTML='<span class=\\'text-red-500 text-xs\\'>Failed to load</span>'">`;
                        } catch(e) {
                            console.error('Error creating preview for photo_after:', e);
                            return '<span class="text-red-500 text-xs">Preview error</span>';
                        }
                    })() : '<span class="text-gray-400 text-xs">No photo</span>'}
                </div>
            </div>
        </div>
        ${breakData.notes ? `<div class="mt-3"><p class="text-xs text-gray-500">Notes:</p><p class="text-sm text-gray-700 mt-1">${breakData.notes}</p></div>` : ''}
        ${breakData.override_reason ? `<div class="mt-2 bg-purple-50 border-l-4 border-purple-400 p-2"><p class="text-xs text-purple-900"><strong>Override Reason:</strong> ${breakData.override_reason}</p></div>` : ''}
    `;

    return card;
}

// Form Submission
document.getElementById('multiBreakForm').addEventListener('submit', (e) => {
    e.preventDefault();

    // Validate we have breaks
    if (breaks.length === 0) {
        alert('Please add at least one break before submitting');
        return;
    }

    // Validate base fields
    const customer = document.getElementById('customer').value;
    const unitNumber = document.getElementById('unit_number').value;
    const repairDate = document.getElementById('repair_date').value;

    if (!customer || !unitNumber || !repairDate) {
        alert('Please fill in all required base information fields');
        return;
    }

    // DIAGNOSTIC: Log submission details BEFORE creating FormData
    console.log('[MULTI-BREAK] Submitting batch:', {
        breaks_count: breaks.length,
        customer: customer,
        unit_number: unitNumber,
        repair_date: repairDate
    });

    const formData = new FormData();

    // Add base fields
    formData.append('customer', customer);
    formData.append('unit_number', unitNumber);
    formData.append('repair_date', repairDate);
    formData.append('breaks_count', breaks.length);

    // Add CSRF token
    formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

    // Add each break's data
    breaks.forEach((breakData, index) => {
        formData.append(`breaks[${index}][damage_type]`, breakData.damage_type);
        formData.append(`breaks[${index}][drilled_before_repair]`, breakData.drilled_before_repair || false);
        formData.append(`breaks[${index}][windshield_temperature]`, breakData.windshield_temperature || '');
        formData.append(`breaks[${index}][resin_viscosity]`, breakData.resin_viscosity || '');
        formData.append(`breaks[${index}][notes]`, breakData.notes || '');
        formData.append(`breaks[${index}][cost_override]`, breakData.cost_override || '');
        formData.append(`breaks[${index}][override_reason]`, breakData.override_reason || '');

        if (breakData.photo_before) {
            formData.append(`breaks[${index}][photo_before]`, breakData.photo_before);
        }
        if (breakData.photo_after) {
            formData.append(`breaks[${index}][photo_after]`, breakData.photo_after);
        }
    });

    // Disable submit button and show loading state
    const submitBtn = document.getElementById('submitAllBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = 'Submitting...';

    // Get CSRF token for headers
    const csrfToken = getCookie('csrftoken');

    // Submit form
    fetch(window.location.href, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',  // Mark as AJAX request
            'X-CSRFToken': csrfToken,  // CSRF token in header for Django
        },
        body: formData,
    })
    .then(response => {
        console.log('[MULTI-BREAK] Response status:', response.status, response.statusText);

        // Clone response so we can read it multiple times if needed
        const clonedResponse = response.clone();

        if (response.ok) {
            return response.json();
        } else {
            // Try to parse error JSON
            return response.json().then(errorData => {
                console.error('[MULTI-BREAK] Server error response:', errorData);
                const errorMsg = errorData.error || `Submission failed (HTTP ${response.status})`;
                const errorType = errorData.error_type || 'Unknown';
                throw new Error(`${errorMsg} [${errorType}]`);
            }).catch(parseError => {
                console.error('[MULTI-BREAK] Failed to parse JSON, trying text:', parseError);
                // Use cloned response to read as text
                return clonedResponse.text().then(text => {
                    console.error('[MULTI-BREAK] Raw error response:', text);
                    throw new Error(`Submission failed (HTTP ${response.status}). Check console for details.`);
                });
            });
        }
    })
    .then(data => {
        console.log('[MULTI-BREAK] Server response data:', data);

        if (data.success) {
            console.log('[MULTI-BREAK] Batch created successfully:', data.batch_id);
            // Clear localStorage on success
            localStorage.removeItem('multiBreakDraft');

            // Show success modal with batch data
            showSuccessModal(data);
        } else {
            throw new Error(data.error || 'Submission failed');
        }
    })
    .catch(error => {
        console.error('[MULTI-BREAK] Submission error:', error);
        alert('Error submitting repairs: ' + error.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = `Submit All Repairs (${breaks.length})`;
    });
});

// LocalStorage Autosave Functions
function saveToLocalStorage() {
    const formState = {
        customer: document.getElementById('customer').value,
        unit_number: document.getElementById('unit_number').value,
        repair_date: document.getElementById('repair_date').value,
        breaks: breaks.map(b => ({
            id: b.id,
            damage_type: b.damage_type,
            notes: b.notes,
            // Can't store File objects, only metadata
            photo_before_name: b.photo_before?.name,
            photo_after_name: b.photo_after?.name
        }))
    };

    try {
        localStorage.setItem('multiBreakDraft', JSON.stringify(formState));
    } catch (e) {
        console.warn('Could not save to localStorage:', e);
    }
}

function restoreFromLocalStorage() {
    try {
        const saved = localStorage.getItem('multiBreakDraft');
        if (saved) {
            const formState = JSON.parse(saved);

            // Ask user if they want to restore
            if (confirm('Found unsaved work. Would you like to restore it?')) {
                document.getElementById('customer').value = formState.customer || '';
                document.getElementById('unit_number').value = formState.unit_number || '';
                document.getElementById('repair_date').value = formState.repair_date || '';

                // Note: Can't restore actual files, user will need to re-upload photos
                // This is a limitation of browser security
            } else {
                localStorage.removeItem('multiBreakDraft');
            }
        }
    } catch (e) {
        console.warn('Could not restore from localStorage:', e);
    }
}

// Success Modal Functions
function showSuccessModal(batchData) {
    const modal = document.getElementById('successModal');

    // Populate modal with batch data
    document.getElementById('success_unit').textContent = batchData.unit_number;
    document.getElementById('success_break_count').textContent = batchData.break_count;
    document.getElementById('success_total_cost').textContent = `$${batchData.total_cost.toFixed(2)}`;

    // Set status badge with appropriate styling
    const statusBadge = document.getElementById('success_status');
    if (batchData.is_auto_approved) {
        statusBadge.textContent = 'Auto-Approved';
        statusBadge.className = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800';
    } else {
        statusBadge.textContent = 'Pending Approval';
        statusBadge.className = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800';
    }

    // Store batch_id for button handlers
    modal.dataset.batchId = batchData.batch_id;

    // Show modal
    modal.classList.add('active');
}

// Success Modal Button Handlers
document.getElementById('startWorkNowBtn').addEventListener('click', function() {
    const modal = document.getElementById('successModal');
    const batchId = modal.dataset.batchId;

    // Start work on all breaks in the batch
    fetch(`/tech/batch/${batchId}/start-work/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Redirect to batch detail page
            window.location.href = `/tech/batch/${batchId}/`;
        } else {
            alert('Error starting work: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error starting work on batch');
    });
});

document.getElementById('viewBatchBtn').addEventListener('click', function() {
    const modal = document.getElementById('successModal');
    const batchId = modal.dataset.batchId;
    window.location.href = `/tech/batch/${batchId}/`;
});

document.getElementById('createAnotherBatchBtn').addEventListener('click', function() {
    const modal = document.getElementById('successModal');
    modal.classList.remove('active');

    // Keep customer selection but clear everything else
    const customer = document.getElementById('customer').value;
    const date = document.getElementById('repair_date').value;

    // Reset form
    document.getElementById('unit_number').value = '';
    breaks = [];
    renderBreaksList();
    updateSubmitButton();
    updatePricingPreview();

    // Restore customer and date
    document.getElementById('customer').value = customer;
    document.getElementById('repair_date').value = date;

    // Re-enable submit button
    const submitBtn = document.getElementById('submitAllBtn');
    submitBtn.disabled = false;
    submitBtn.innerHTML = 'Submit All Repairs (0)';
});
