// Simple, guaranteed-to-work status chart
console.log('Simple Status Chart: Loading...');

function createSimpleStatusChart() {
    console.log('Simple Status Chart: Creating chart...');
    
    const container = document.getElementById('status-chart');
    if (!container) {
        console.error('Simple Status Chart: Container not found');
        return;
    }
    
    // Clear any existing content
    container.innerHTML = '';
    
    // Get data from stats elements
    const getStatValue = (id) => {
        const el = document.getElementById(id);
        return el ? parseInt(el.textContent) || 0 : 0;
    };
    
    const data = {
        REQUESTED: getStatValue('stats-requested'),
        PENDING: getStatValue('stats-pending'),
        APPROVED: getStatValue('stats-approved'),
        IN_PROGRESS: getStatValue('stats-in-progress'),
        COMPLETED: getStatValue('stats-completed'),
        DENIED: getStatValue('stats-denied')
    };
    
    console.log('Simple Status Chart: Data:', data);
    
    // Create a simple HTML chart
    const chartHTML = `
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h4 style="text-align: center; margin-bottom: 20px; color: #333;">Repair Status Distribution</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                ${Object.entries(data).map(([status, count]) => {
                    if (count === 0) return '';
                    
                    const colors = {
                        REQUESTED: '#6c757d',
                        PENDING: '#ffc107', 
                        APPROVED: '#17a2b8',
                        IN_PROGRESS: '#007bff',
                        COMPLETED: '#28a745',
                        DENIED: '#dc3545'
                    };
                    
                    const color = colors[status] || '#ccc';
                    const label = status.replace('_', ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
                    
                    return `
                        <div style="
                            background: ${color}; 
                            color: white; 
                            padding: 15px; 
                            border-radius: 8px; 
                            text-align: center;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        ">
                            <div style="font-size: 24px; font-weight: bold; margin-bottom: 5px;">${count}</div>
                            <div style="font-size: 12px; opacity: 0.9;">${label}</div>
                        </div>
                    `;
                }).join('')}
            </div>
            <div style="text-align: center; margin-top: 20px; padding: 10px; background: #f8f9fa; border-radius: 4px; color: #666;">
                Total Repairs: ${Object.values(data).reduce((sum, count) => sum + count, 0)}
            </div>
        </div>
    `;
    
    container.innerHTML = chartHTML;
    console.log('Simple Status Chart: Chart created successfully');
}

// Try multiple ways to ensure the chart loads
document.addEventListener('DOMContentLoaded', createSimpleStatusChart);
setTimeout(createSimpleStatusChart, 500);
setTimeout(createSimpleStatusChart, 1000);

// Expose globally so it can be called from tab navigation
window.createSimpleStatusChart = createSimpleStatusChart;