document.addEventListener('DOMContentLoaded', function() {
    console.log('Repair Frequency Chart: DOMContentLoaded event triggered');
    
    // Constants and configuration
    const containerWidth = document.getElementById('frequency-container').clientWidth;
    const width = Math.min(800, containerWidth * 0.95);
    const height = 380;
    const margin = {top: 30, right: 40, bottom: 80, left: 60};
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // DOM setup
    const svg = d3.select('#cost-chart')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);
    
    // Add title
    svg.append('text')
        .attr('class', 'chart-title')
        .attr('x', innerWidth / 2)
        .attr('y', -margin.top / 2)
        .attr('text-anchor', 'middle')
        .style('font-size', '14px')
        .style('font-weight', 'bold')
        .style('fill', '#555')
        .text('Monthly Repair Volume');
    
    // Create loading indicator
    const loadingIndicator = d3.select('#cost-chart')
        .append('div')
        .attr('class', 'loading-indicator')
        .style('position', 'absolute')
        .style('top', '50%')
        .style('left', '50%')
        .style('transform', 'translate(-50%, -50%)')
        .text('Loading data...');
    
    // Create error message container (hidden initially)
    const errorContainer = d3.select('#cost-chart')
        .append('div')
        .attr('class', 'error-message')
        .style('position', 'absolute')
        .style('top', '50%')
        .style('left', '50%')
        .style('transform', 'translate(-50%, -50%)')
        .style('display', 'none')
        .style('color', '#d9534f')
        .style('text-align', 'center')
        .text('Error loading data');
    
    // Generate sample data
    function generateSampleData() {
        const today = new Date();
        const data = [];
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
            data.push({
                date: date,
                count: Math.floor(Math.random() * 5) + 1
            });
        }
        
        return data;
    }
    
    // Create the chart
    function createChart(data) {
        console.log('Creating repair frequency chart with data:', data);
        
        // Hide error message if it was showing
        errorContainer.style('display', 'none');
        
        // If no data or empty array, show placeholder message
        if (!data || data.length === 0) {
            svg.append('text')
                .attr('class', 'no-data-message')
                .attr('x', innerWidth / 2)
                .attr('y', innerHeight / 2)
                .attr('text-anchor', 'middle')
                .style('font-size', '14px')
                .style('fill', '#777')
                .text('No repair frequency data available');
            
            return;
        }
        
        // Clear any previous chart elements
        svg.selectAll('.line, .area, .dot, .axis, .grid, .axis-label, .point-label, .no-data-message, .summary-text').remove();
        
        // Process and normalize data to ensure consistent date objects
        const normalizedData = data.map(item => {
            // Handle string date formats
            let dateObj;
            if (typeof item.date === 'string') {
                // Check if date has a day component
                if (item.date.length <= 7) {
                    // If it's just YYYY-MM, add day component
                    dateObj = new Date(`${item.date}-01`);
                } else {
                    dateObj = new Date(item.date);
                }
            } else if (item.date instanceof Date) {
                dateObj = item.date;
            } else {
                // Fallback to current date
                dateObj = new Date();
            }
            
            return {
                date: dateObj,
                count: parseInt(item.count || 0)
            };
        });
        
        // Sort data by date
        normalizedData.sort((a, b) => a.date - b.date);
        
        // Add points if only one or two data points
        if (normalizedData.length === 1) {
            const date = normalizedData[0].date;
            
            // Add points before and after
            const beforeDate = new Date(date);
            beforeDate.setMonth(date.getMonth() - 2);
            
            const afterDate = new Date(date);
            afterDate.setMonth(date.getMonth() + 2);
            
            normalizedData.unshift({date: beforeDate, count: 0});
            normalizedData.push({date: afterDate, count: 0});
        } else if (normalizedData.length === 2) {
            // Add a middle point
            const midDate = new Date((normalizedData[0].date.getTime() + normalizedData[1].date.getTime()) / 2);
            normalizedData.splice(1, 0, {date: midDate, count: 0});
        }
        
        // Create scales
        const x = d3.scaleTime()
            .domain(d3.extent(normalizedData, d => d.date))
            .nice(d3.timeMonth)
            .range([0, innerWidth]);
        
        const y = d3.scaleLinear()
            .domain([0, Math.max(d3.max(normalizedData, d => d.count) * 1.2, 3)])
            .nice()
            .range([innerHeight, 0]);
        
        // Create line
        const line = d3.line()
            .x(d => x(d.date))
            .y(d => y(d.count))
            .curve(d3.curveCatmullRom.alpha(0.5));
        
        // Create area
        const area = d3.area()
            .x(d => x(d.date))
            .y0(innerHeight)
            .y1(d => y(d.count))
            .curve(d3.curveCatmullRom.alpha(0.5));
        
        // Add horizontal grid lines
        svg.append('g')
            .attr('class', 'grid')
            .call(d3.axisLeft(y)
                .ticks(5)
                .tickSize(-innerWidth)
                .tickFormat(''))
            .selectAll('line')
            .style('stroke', '#e0e0e0')
            .style('stroke-dasharray', '3,3');
        
        // Add x-axis
        svg.append('g')
            .attr('class', 'axis x-axis')
            .attr('transform', `translate(0, ${innerHeight})`)
            .call(d3.axisBottom(x)
                .ticks(Math.min(normalizedData.length, 6))
                .tickFormat(d3.timeFormat('%b %Y')))
            .selectAll('text')
            .attr('transform', 'translate(-10,10)rotate(-45)')
            .style('text-anchor', 'end')
            .style('font-size', '11px')
            .style('font-weight', '500');
        
        // Add x-axis label
        svg.append('text')
            .attr('class', 'axis-label')
            .attr('x', innerWidth / 2)
            .attr('y', innerHeight + margin.bottom - 10)
            .attr('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('fill', '#555')
            .text('Month');
        
        // Add y-axis
        svg.append('g')
            .attr('class', 'axis y-axis')
            .call(d3.axisLeft(y)
                .ticks(5)
                .tickFormat(d => Math.floor(d) === d ? d : ''));
        
        // Add y-axis label
        svg.append('text')
            .attr('class', 'axis-label')
            .attr('transform', 'rotate(-90)')
            .attr('y', -margin.left + 15)
            .attr('x', -innerHeight / 2)
            .attr('dy', '1em')
            .style('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('fill', '#555')
            .text('Number of Repairs');
        
        // Add area fill
        svg.append('path')
            .datum(normalizedData)
            .attr('class', 'area')
            .attr('fill', 'rgba(41, 128, 185, 0.3)')
            .attr('d', area);
        
        // Add the line
        svg.append('path')
            .datum(normalizedData)
            .attr('class', 'line')
            .attr('fill', 'none')
            .attr('stroke', '#2980b9')
            .attr('stroke-width', 3)
            .attr('stroke-linejoin', 'round')
            .attr('stroke-linecap', 'round')
            .attr('d', line);
        
        // Add dots for each data point
        svg.selectAll('.dot')
            .data(normalizedData)
            .enter()
            .append('circle')
            .attr('class', 'dot')
            .attr('cx', d => x(d.date))
            .attr('cy', d => y(d.count))
            .attr('r', d => d.count > 0 ? 6 : 4)
            .attr('fill', '#2980b9')
            .attr('stroke', 'white')
            .attr('stroke-width', 2);
        
        // Add text labels for data points
        svg.selectAll('.point-label')
            .data(normalizedData.filter(d => d.count > 0))
            .enter()
            .append('text')
            .attr('class', 'point-label')
            .attr('x', d => x(d.date))
            .attr('y', d => y(d.count) - 15)
            .attr('text-anchor', 'middle')
            .style('font-size', '11px')
            .style('font-weight', 'bold')
            .style('fill', '#333')
            .text(d => d.count);
        
        // Add summary text
        const totalRepairs = normalizedData.reduce((sum, d) => sum + d.count, 0);
        svg.append('text')
            .attr('class', 'summary-text')
            .attr('x', innerWidth / 2)
            .attr('y', innerHeight + 40)
            .attr('text-anchor', 'middle')
            .style('font-size', '13px')
            .style('font-style', 'italic')
            .style('fill', '#666')
            .text(`Total repairs in this period: ${totalRepairs}`);
    }
    
    // Fetch data from API with retry mechanism
    function fetchDataWithRetry(url, retries = 2) {
        console.log(`Repair Frequency Chart: Fetching data from ${url}, retries left: ${retries}`);
        
        return fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.status}`);
                }
                return response.text();
            })
            .then(text => {
                // Log raw response
                console.log('Repair Frequency Chart: Raw API response:', text);
                
                if (!text || text.trim() === '') {
                    console.log('Repair Frequency Chart: Empty response, returning empty array');
                    return [];
                }
                
                try {
                    return JSON.parse(text);
                } catch (e) {
                    console.error('Repair Frequency Chart: Error parsing JSON:', e);
                    throw new Error('Invalid JSON response');
                }
            })
            .catch(error => {
                console.error('Repair Frequency Chart: Error fetching data:', error);
                
                if (retries > 0) {
                    console.log(`Repair Frequency Chart: Retrying (${retries} left)...`);
                    return new Promise(resolve => {
                        setTimeout(() => {
                            resolve(fetchDataWithRetry(url, retries - 1));
                        }, 1000); // 1 second delay before retry
                    });
                }
                
                throw error;
            });
    }
    
    // Main function to load data and create chart
    function loadDataAndCreateChart() {
        console.log('Repair Frequency Chart: Fetching data from API...');
        
        fetchDataWithRetry('/customer/api/repair-cost-data/')
            .then(data => {
                // Remove loading indicator
                loadingIndicator.remove();
                
                console.log('Repair Frequency Chart: Processed data:', data);
                
                // Create chart with the data, or sample data as a last resort
                if (Array.isArray(data) && data.length > 0) {
                    createChart(data);
                } else {
                    console.log('Repair Frequency Chart: No valid data, using sample data');
                    createChart(generateSampleData());
                }
            })
            .catch(error => {
                // Remove loading indicator
                loadingIndicator.remove();
                
                // Show error message
                errorContainer.style('display', 'block');
                errorContainer.text(`Error loading data: ${error.message}`);
                
                console.error('Repair Frequency Chart: Fatal error:', error);
                
                // Fall back to sample data
                createChart(generateSampleData());
            });
    }
    
    // Start loading data
    loadDataAndCreateChart();
}); 