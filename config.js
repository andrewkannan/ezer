// EZER site configuration
// ---------------------------------------------------------------------------
// Edit these values to update the live site. Empty values are handled
// gracefully: the related button/section is simply hidden until it is set.
// The Admin panel (admin.html) can preview changes locally via localStorage;
// copy final values here to publish them for everyone.
// ---------------------------------------------------------------------------
const EZER_CONFIG = {
    // --- Lead capture -------------------------------------------------------
    // WhatsApp number in international format, digits only (e.g. "60123456789").
    whatsappNumber: "601160547134",
    // Pre-filled WhatsApp message for the "Chat on WhatsApp" buttons.
    whatsappMessage: "Hi EZER, I'd like a free workflow check for my business.",
    // Public business email shown on the site (optional).
    contactEmail: "",
    // Web3Forms access key (free at https://web3forms.com). Form submissions
    // are emailed to the address you register there. This key is designed to
    // be public, so it is safe to keep in client-side code.
    web3formsKey: "",

    // --- Founder & booking --------------------------------------------------
    // Founder photo inside this repo, e.g. "assets/kenisha.jpg". While empty,
    // a gold "K" monogram is shown instead.
    founderPhoto: "",
    linkedinUrl: "",
    calendlyUrl: "",
    // YouTube embed URL, e.g. "https://www.youtube.com/embed/VIDEO_ID"
    founderVideoUrl: "",
    leadMagnetPdfUrl: "",

    // --- Analytics (optional) ---------------------------------------------
    // Leave empty to keep the site analytics-free. When set, visitors see a
    // short consent bar and tracking starts only after they press Accept.
    // Google Analytics 4 measurement ID, e.g. "G-ABC123XYZ"
    ga4Id: "",
    // Meta (Facebook/Instagram) Pixel ID, digits only
    metaPixelId: "",

    // --- Optional content (sections stay hidden while these are empty) ------
    showFaq: true,
    // Real client results only, e.g. { client: "Clinic in JB", metric: "+35%", description: "More bookings from WhatsApp enquiries." }
    caseStudies: [],
    // Real client logo image URLs only.
    logos: []
};

// Local preview overrides saved from the Admin panel.
try {
    const savedConfig = localStorage.getItem('ezer_admin_config');
    if (savedConfig) Object.assign(EZER_CONFIG, JSON.parse(savedConfig));
} catch (err) {
    console.warn('EZER: ignoring invalid admin preview config', err);
}
