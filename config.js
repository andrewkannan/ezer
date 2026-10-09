// EZER Configuration Panel
// Edit these values to update the live site
const EZER_CONFIG = {
    linkedinUrl: "https://linkedin.com/in/dummy-profile",
    calendlyUrl: "https://calendly.com/dummy-account",
    founderVideoUrl: "https://www.youtube.com/embed/dQw4w9WgXcQ", // Dummy video
    leadMagnetPdfUrl: "https://dummy-pdf-link.com/audit.pdf",
    
    // Case Studies
    caseStudies: [
        { client: "TechCorp", metric: "+45%", description: "Increase in lead conversion rate." },
        { client: "LocalAgency", metric: "20hrs", description: "Saved per week on admin tasks." },
        { client: "EcomStore", metric: "100%", description: "Follow-up rate achieved." }
    ],
    
    // Logos for ticker (Using dummy image URLs)
    logos: [
        "https://via.placeholder.com/150x50/f7f4ed/17221f?text=CLIENT+ONE",
        "https://via.placeholder.com/150x50/f7f4ed/17221f?text=CLIENT+TWO",
        "https://via.placeholder.com/150x50/f7f4ed/17221f?text=CLIENT+THREE",
        "https://via.placeholder.com/150x50/f7f4ed/17221f?text=CLIENT+FOUR"
    ]
};

// If local storage has overrides from the Admin Panel, use those instead
const savedConfig = localStorage.getItem('ezer_admin_config');
if (savedConfig) {
    Object.assign(EZER_CONFIG, JSON.parse(savedConfig));
}
