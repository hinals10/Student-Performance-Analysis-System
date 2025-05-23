document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const sidebar = document.querySelector('.sidebar');
    const menuItems = document.querySelectorAll('.menu li');
    const contentSections = document.querySelectorAll('.content-section');
    const logoutBtn = document.querySelector('.logout');
    const searchBox = document.querySelector('.search-box input');
    const notificationBell = document.querySelector('.notification');
    const profileImg = document.querySelector('.profile-img');
    
    // Modal Elements
    const modals = document.querySelectorAll('.modal');
    const closeModalBtns = document.querySelectorAll('.close-modal');
    const addStudentBtn = document.getElementById('add-student-btn');
    const addFacultyBtn = document.getElementById('add-faculty-btn');
    const addBatchBtn = document.getElementById('add-batch-btn');
    const addSemesterBtn = document.getElementById('add-semester-btn');
    const addSubjectBtn = document.getElementById('add-subject-btn');
    const confirmModal = document.getElementById('confirm-modal');
    const confirmActionBtn = document.getElementById('confirm-action');
    
    // Tab Elements
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Filter Elements
    const batchFilter = document.getElementById('batch-filter');
    const semesterFilter = document.getElementById('semester-filter');
    const departmentFilter = document.getElementById('department-filter');
    const refreshStudentsBtn = document.getElementById('refresh-students');
    const refreshFacultyBtn = document.getElementById('refresh-faculty');
    
    // Report Elements
    const reportType = document.getElementById('report-type');
    const batchSelect = document.getElementById('batch-select');
    const performanceChart = document.getElementById('performance-chart');
    
    // CSRF Token for AJAX requests
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Current active section
    let currentSection = 'dashboard';
    
    // Initialize the dashboard
    initDashboard();
    
    function initDashboard() {
        // Set up event listeners
        setupEventListeners();
        
        // Initialize charts
        initCharts();
        
        // Show the active section
        showSection(currentSection);
    }
    
    function setupEventListeners() {
        // Sidebar navigation
        menuItems.forEach(item => {
            item.addEventListener('click', function() {
                const section = this.getAttribute('data-section');
                showSection(section);
                
                // Update active state
                menuItems.forEach(i => i.classList.remove('active'));
                this.classList.add('active');
                
                currentSection = section;
            });
        });
        
        // Logout button
        logoutBtn.addEventListener('click', function() {
            window.location.href = '/login/';
        });
        
        // Search functionality
        searchBox.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            filterTables(searchTerm);
        });
        
        // Notification bell
        notificationBell.addEventListener('click', function() {
            alert('You have 3 new notifications');
        });
        
        // Profile image click
        profileImg.addEventListener('click', function() {
            alert('Profile options would appear here');
        });
        
        // Modal handling
        addStudentBtn?.addEventListener('click', () => {
            showModal('add-student-modal');
            document.getElementById('add-student-form').reset();
        });
        addFacultyBtn?.addEventListener('click', () => showModal('add-faculty-modal'));
        addBatchBtn?.addEventListener('click', () => showModal('add-batch-modal'));
        addSemesterBtn?.addEventListener('click', () => showModal('add-semester-modal'));
        addSubjectBtn?.addEventListener('click', () => {
            console.log('Add subject modal');
            showModal('add-subject-modal');
        });
        
        closeModalBtns.forEach(btn => {
            btn.addEventListener('click', closeAllModals);
        });
        
        // Close modal when clicking outside
        modals.forEach(modal => {
            modal.addEventListener('click', function(e) {
                if (e.target === this) {
                    closeAllModals();
                }
            });
        });
        
        // Confirm modal action
        confirmActionBtn.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            const id = this.getAttribute('data-id');
            
            if (action === 'delete-student') {
                deleteStudent(id);
            } else if (action === 'delete-faculty') {
                deleteFaculty(id);
            }
            
            closeAllModals();
        });
        
        // Tab switching
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const tabId = this.getAttribute('data-tab');
                
                // Update active tab button
                tabBtns.forEach(tab => tab.classList.remove('active'));
                this.classList.add('active');
                
                // Show corresponding tab content
                tabContents.forEach(content => {
                    if (content.id === `${tabId}-tab`) {
                        content.classList.add('active');
                    } else {
                        content.classList.remove('active');
                    }
                });
            });
        });
        
        // Filter functionality
        batchFilter?.addEventListener('change', filterStudents);
        semesterFilter?.addEventListener('change', filterStudents);
        departmentFilter?.addEventListener('change', filterFaculty);
        
        
        
        // Edit and Delete buttons in tables
        document.addEventListener('click', function(e) {
            if (e.target.closest('.btn-edit')) {
                const btn = e.target.closest('.btn-edit');
                const id = btn.getAttribute('data-id');
                const section = currentSection;
                
                if (section === 'student-management') {
                    editStudent(id);
                } else if (section === 'faculty-management') {
                    editFaculty(id);
                } else if (section === 'batch-management') {
                    editBatch(id);
                }
            }
            
            if (e.target.closest('.btn-danger')) {
                const btn = e.target.closest('.btn-danger');
                const id = btn.getAttribute('data-id');
                const section = currentSection;
                
                if (section === 'student-management') {
                    showConfirmModal(
                        'Delete Student', 
                        'Are you sure you want to delete this student? This action cannot be undone.',
                        'delete-student',
                        id
                    );
                } else if (section === 'faculty-management') {
                    showConfirmModal(
                        'Delete Faculty', 
                        'Are you sure you want to delete this faculty member? This action cannot be undone.',
                        'delete-faculty',
                        id
                    );
                }
            }
        });
        
        const addFacultyForm = document.getElementById('add-faculty-form');
        if (addFacultyForm) {
            addFacultyForm.addEventListener('submit', function(e) {
                e.preventDefault();
                addFaculty();
            });
        }
    }
    
    function showSection(section) {
        contentSections.forEach(sec => {
            if (sec.id === `${section}-section`) {
                sec.classList.add('active');
                if (section === 'reports' && typeof Chart !== 'undefined') {
                    renderCharts();
                }
            } else {
                sec.classList.remove('active');
            }
        });
    }
    
    function showModal(modalId) {
        closeAllModals();
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        } else {
            console.error(`Modal with ID ${modalId} not found`);
        }
    }
    
    function closeAllModals() {
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
    }
    
    function showConfirmModal(title, message, action, id) {
        document.getElementById('confirm-title').textContent = title;
        document.getElementById('confirm-message').textContent = message;
        confirmActionBtn.setAttribute('data-action', action);
        confirmActionBtn.setAttribute('data-id', id);
        showModal('confirm-modal');
    }
    
    function filterTables(searchTerm) {
        const tables = document.querySelectorAll('.table-container table');
        
        tables.forEach(table => {
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    function filterStudents() {
        const batchValue = batchFilter.value;
        const semesterValue = semesterFilter.value;
        const rows = document.querySelectorAll('#students-table tbody tr');
        
        rows.forEach(row => {
            const batchMatch = batchValue === 'all' || row.cells[3].textContent === batchFilter.options[batchFilter.selectedIndex].text;
            const semesterMatch = semesterValue === 'all' || row.cells[4].textContent === semesterFilter.options[semesterFilter.selectedIndex].text;
            
            if (batchMatch && semesterMatch) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    function filterFaculty() {
        const departmentValue = departmentFilter.value;
        const rows = document.querySelectorAll('#faculty-table tbody tr');
        
        rows.forEach(row => {
            const departmentMatch = departmentValue === 'all' || row.cells[3].textContent === departmentFilter.options[departmentFilter.selectedIndex].text;
            
            if (departmentMatch) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    function refreshStudents() {
        console.log('Refreshing student data...');
        filterStudents();
    }
    
    function refreshFaculty() {
        console.log('Refreshing faculty data...');
        filterFaculty();
    }
    
    function editStudent(id) {
        console.log(`Editing student with ID: ${id}`);
        showModal('add-student-modal');
    }
    
    function deleteStudent(id) {
        console.log(`Deleting student with ID: ${id}`);
        const row = document.querySelector(`#students-table tbody tr td:first-child:contains("${id}")`)?.parentNode;
        if (row) row.remove();
    }
    
    function addFaculty() {
        const form = document.getElementById('add-faculty-form');
        const formData = new FormData(form);
        
        console.log('Faculty data:', Object.fromEntries(formData.entries()));
        alert('Adding new faculty member...');
        
        closeAllModals();
        form.reset();
        refreshFaculty();
    }
    
    function editFaculty(id) {
        console.log(`Editing faculty with ID: ${id}`);
        showModal('add-faculty-modal');
    }
    
    function editBatch(id) {
        console.log(`Editing batch with ID: ${id}`);
    }
    
    function initCharts() {
        if (!performanceChart || typeof Chart === 'undefined') {
            console.error('Performance chart or Chart.js not available');
            return;
        }
        
        const ctx = performanceChart.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Semester 1', 'Semester 2', 'Semester 3', 'Semester 4', 'Semester 5', 'Semester 6'],
                datasets: [{
                    label: 'Average Score',
                    data: [75, 78, 82, 80, 85, 88],
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 50,
                        max: 100
                    }
                }
            }
        });
    }
    
    function renderCharts() {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js not loaded');
            return;
        }

        const courseAvgCgpaCtx = document.getElementById('courseAvgCgpaChart')?.getContext('2d');
        const semesterAvgCgpaCtx = document.getElementById('semesterAvgCgpaChart')?.getContext('2d');

        if (courseAvgCgpaCtx) {
            new Chart(courseAvgCgpaCtx, {
                type: 'bar',
                data: {
                    labels: ['BCA', 'BSCIT', 'MCA', 'MSCIT'],
                    datasets: [{
                        label: 'Average CGPA',
                        data: [7.5, 8.0, 7.8, 8.2],
                        backgroundColor: 'rgba(2, 119, 189, 0.5)',
                        borderColor: 'rgba(2, 119, 189, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        } else {
            console.error('Course CGPA chart canvas not found');
        }

        if (semesterAvgCgpaCtx) {
            new Chart(semesterAvgCgpaCtx, {
                type: 'line',
                data: {
                    labels: ['Semester 1', 'Semester 2', 'Semester 3', 'Semester 4', 'Semester 5', 'Semester 6'],
                    datasets: [
                        {
                            label: 'BCA',
                            data: [7.0, 7.2, 7.4, 7.6, 7.8, 8.0],
                            borderColor: 'rgba(2, 119, 189, 1)',
                            fill: false
                        },
                        {
                            label: 'BSCIT',
                            data: [7.5, 7.6, 7.7, 7.8, 7.9, 8.0],
                            borderColor: 'rgba(255, 99, 132, 1)',
                            fill: false
                        },
                        {
                            label: 'MCA',
                            data: [7.2, 7.4, 7.6, 7.8, 8.0, 8.2],
                            borderColor: 'rgba(75, 192, 192, 1)',
                            fill: false
                        },
                        {
                            label: 'MSCIT',
                            data: [7.8, 8.0, 8.2, 8.4, 8.6, 8.8],
                            borderColor: 'rgba(153, 102, 255, 1)',
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        } else {
            console.error('Semester CGPA chart canvas not found');
        }
    }
    
    HTMLElement.prototype.containsText = function(text) {
        return this.textContent.toLowerCase().includes(text.toLowerCase());
    };
});