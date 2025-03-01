document.addEventListener('DOMContentLoaded', function () {
    const button = document.querySelector('button[aria-expanded]');
    const menu = document.querySelector('.absolute.top-full');
  
    button.addEventListener('click', function () {
      const isExpanded = button.getAttribute('aria-expanded') === 'true';
      button.setAttribute('aria-expanded', !isExpanded);
  
      // Toggle the visibility of the menu with transitions
      if (!isExpanded) {
        menu.classList.remove('opacity-0', 'translate-y-1');
        menu.classList.add('opacity-100', 'translate-y-0');
      } else {
        menu.classList.remove('opacity-100', 'translate-y-0');
        menu.classList.add('opacity-0', 'translate-y-1');
      }
    });
  });

  document.addEventListener('DOMContentLoaded', function () {
    // Select elements for mobile menu
    const openMenuButton = document.querySelector('button[aria-label="Open main menu"]');
    const closeMenuButton = document.querySelector('button[aria-label="Close menu"]');
    const mobileMenu = document.querySelector('.fixed.inset-y-0.right-0'); // Mobile menu container
    const backdrop = document.querySelector('.fixed.inset-0.z-10'); // Backdrop
  
    // Select elements for dropdown menu
    const dropdownButton = document.querySelector('button[aria-controls="disclosure-1"]');
    const dropdownMenu = document.querySelector('#disclosure-1');
  
    // Function to open the mobile menu
    function openMobileMenu() {
      mobileMenu.classList.remove('translate-x-full'); // Slide in the menu
      backdrop.classList.remove('hidden'); // Show the backdrop
      document.body.classList.add('overflow-hidden'); // Prevent scrolling
    }
  
    // Function to close the mobile menu
    function closeMobileMenu() {
      mobileMenu.classList.add('translate-x-full'); // Slide out the menu
      backdrop.classList.add('hidden'); // Hide the backdrop
      document.body.classList.remove('overflow-hidden'); // Allow scrolling
    }
  
    // Function to toggle the dropdown menu
    function toggleDropdownMenu() {
      const isExpanded = dropdownButton.getAttribute('aria-expanded') === 'true';
      dropdownButton.setAttribute('aria-expanded', !isExpanded);
      dropdownMenu.classList.toggle('hidden'); // Toggle visibility of the dropdown menu
    }
  
    // Open mobile menu on button click
    openMenuButton.addEventListener('click', openMobileMenu);
  
    // Close mobile menu on close button click
    closeMenuButton.addEventListener('click', closeMobileMenu);
  
    // Close mobile menu when clicking outside (on the backdrop)
    backdrop.addEventListener('click', closeMobileMenu);
  
    // Toggle dropdown menu on button click
    dropdownButton.addEventListener('click', toggleDropdownMenu);
  });