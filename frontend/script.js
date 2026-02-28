/**
 * CSSC - Cyber Security Students Club
 * Main JavaScript File
 * Handles: animated background, navbar, scroll reveal, typing effect,
 *          counter animation, accordion, form validation, team contacts
 */

/* ============================================================
   1. ANIMATED CYBER BACKGROUND CANVAS
   ============================================================ */
(function initCyberBackground() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let W, H, particles = [], connections = [];

    function resize() {
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }

    // Particle class
    class Particle {
        constructor() { this.reset(); }
        reset() {
            this.x = Math.random() * W;
            this.y = Math.random() * H;
            this.vx = (Math.random() - 0.5) * 0.4;
            this.vy = (Math.random() - 0.5) * 0.4;
            this.r = Math.random() * 2 + 0.5;
            this.alpha = Math.random() * 0.5 + 0.1;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < 0 || this.x > W) this.vx *= -1;
            if (this.y < 0 || this.y > H) this.vy *= -1;
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 255, 136, ${this.alpha})`;
            ctx.fill();
        }
    }

    function initParticles(count = 80) {
        particles = [];
        for (let i = 0; i < count; i++) particles.push(new Particle());
    }

    function drawConnections() {
        const maxDist = 130;
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < maxDist) {
                    const opacity = (1 - dist / maxDist) * 0.15;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(0, 255, 136, ${opacity})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
    }

    // Floating binary / hex characters
    const chars = ['0', '1', 'A', 'B', 'C', 'D', 'E', 'F', '7', '3'];
    const floatChars = [];
    for (let i = 0; i < 25; i++) {
        floatChars.push({
            char: chars[Math.floor(Math.random() * chars.length)],
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            speed: Math.random() * 0.5 + 0.2,
            alpha: Math.random() * 0.04 + 0.01,
            size: Math.random() * 10 + 8
        });
    }

    function drawFloatChars() {
        ctx.font = 'Share Tech Mono, monospace';
        floatChars.forEach(fc => {
            ctx.font = `${fc.size}px "Share Tech Mono", monospace`;
            ctx.fillStyle = `rgba(0, 255, 136, ${fc.alpha})`;
            ctx.fillText(fc.char, fc.x, fc.y);
            fc.y += fc.speed;
            if (fc.y > H + 20) {
                fc.y = -20;
                fc.x = Math.random() * W;
                fc.char = chars[Math.floor(Math.random() * chars.length)];
            }
        });
    }

    function animate() {
        ctx.clearRect(0, 0, W, H);
        drawFloatChars();
        particles.forEach(p => { p.update(); p.draw(); });
        drawConnections();
        requestAnimationFrame(animate);
    }

    resize();
    initParticles();
    animate();
    window.addEventListener('resize', () => { resize(); });
})();


/* ============================================================
   2. NAVBAR – scroll effect + hamburger mobile menu
   ============================================================ */
(function initNavbar() {
    const navbar = document.getElementById('navbar');
    const hamburger = document.getElementById('hamburger');
    const mobileNav = document.getElementById('mobile-nav');

    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle('scrolled', window.scrollY > 20);
        });
    }

    if (hamburger && mobileNav) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('open');
            mobileNav.classList.toggle('open');
        });

        // Close on link click
        mobileNav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('open');
                mobileNav.classList.remove('open');
            });
        });
    }
})();


/* ============================================================
   3. SCROLL REVEAL ANIMATION
   ============================================================ */
(function initScrollReveal() {
    const elements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
                // Stagger delay based on sibling index
                const siblings = entry.target.parentElement.querySelectorAll('.reveal, .reveal-left, .reveal-right');
                let idx = Array.from(siblings).indexOf(entry.target);
                entry.target.style.transitionDelay = `${Math.min(idx * 0.08, 0.5)}s`;
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); // animate only once
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    elements.forEach(el => observer.observe(el));
})();


/* ============================================================
   4. HERO TYPING EFFECT
   ============================================================ */
(function initTypingEffect() {
    const el = document.getElementById('typing-tagline');
    if (!el) return;

    const taglines = [
        '// SECURE · ETHICAL · VIGILANT',
        '// HACK THE LEARNING CURVE',
        '// DEFEND · DETECT · RESPOND',
        '// KNOWLEDGE IS THE BEST FIREWALL',
        '// CTF · LABS · WORKSHOPS · COMMUNITY'
    ];

    let tagIdx = 0;
    let charIdx = 0;
    let isDeleting = false;
    let typingSpeed = 60;

    el.classList.add('typing-cursor');

    function type() {
        const current = taglines[tagIdx % taglines.length];
        if (isDeleting) {
            el.textContent = current.substring(0, charIdx - 1);
            charIdx--;
            typingSpeed = 30;
        } else {
            el.textContent = current.substring(0, charIdx + 1);
            charIdx++;
            typingSpeed = 60;
        }

        if (!isDeleting && charIdx === current.length) {
            typingSpeed = 2500; // pause at end
            isDeleting = true;
        } else if (isDeleting && charIdx === 0) {
            isDeleting = false;
            tagIdx++;
            typingSpeed = 400;
        }

        setTimeout(type, typingSpeed);
    }

    setTimeout(type, 1200);
})();


/* ============================================================
   5. COUNTER ANIMATION (stats section)
   ============================================================ */
(function initCounters() {
    const counters = document.querySelectorAll('.stat-number[data-target]');
    if (!counters.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseInt(el.dataset.target, 10);
                const duration = 1600;
                const startTime = performance.now();

                function animate(now) {
                    const elapsed = now - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    // Ease-out cubic
                    const eased = 1 - Math.pow(1 - progress, 3);
                    const current = Math.round(eased * target);
                    el.textContent = current;
                    if (progress < 1) {
                        requestAnimationFrame(animate);
                    } else {
                        el.textContent = target + '+';
                    }
                }

                requestAnimationFrame(animate);
                observer.unobserve(el);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(c => observer.observe(c));
})();


/* ============================================================
   6. ACCORDION (Policies page)
   ============================================================ */
function toggleAccordion(btn) {
    const item = btn.closest('.accordion-item');
    const body = item.querySelector('.accordion-body');
    const isOpen = item.classList.contains('open');

    // Close all
    document.querySelectorAll('.accordion-item.open').forEach(openItem => {
        openItem.classList.remove('open');
        openItem.querySelector('.accordion-body').style.maxHeight = '0';
    });

    // Open clicked (if was closed)
    if (!isOpen) {
        item.classList.add('open');
        body.style.maxHeight = body.scrollHeight + 'px';
    }
}

// Auto-open accordion from hash
(function openAccordionFromHash() {
    const hash = window.location.hash;
    if (!hash) return;
    const target = document.querySelector(hash);
    if (target && target.classList.contains('accordion-item')) {
        setTimeout(() => {
            const btn = target.querySelector('.accordion-header');
            if (btn) { toggleAccordion(btn); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
        }, 400);
    }
})();


/* ============================================================
   7. TEAM CONTACT TOGGLE
   ============================================================ */
function toggleEmail(btn) {
    const emailDiv = btn.nextElementSibling;
    if (!emailDiv) return;
    if (emailDiv.classList.contains('show')) {
        emailDiv.classList.remove('show');
        btn.textContent = 'Show Contact';
    } else {
        emailDiv.classList.add('show');
        btn.textContent = 'Hide Contact';
    }
}


/* ============================================================
   8. REGISTRATION FORM – Validation & Submission
   ============================================================ */
(function initRegisterForm() {
    const form = document.getElementById('register-form');
    if (!form) return;

    const BACKEND_URL = 'http://127.0.0.1:5000'; // Change to deployed URL when live

    // Helper: sanitize input to prevent XSS
    function sanitize(str) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // Validation helpers
    function setFieldError(fieldId, msgId, message) {
        const field = document.getElementById(fieldId);
        const msg = document.getElementById(msgId);
        if (field) field.classList.add('invalid');
        if (msg) msg.textContent = message;
        return false;
    }

    function clearFieldError(fieldId, msgId) {
        const field = document.getElementById(fieldId);
        const msg = document.getElementById(msgId);
        if (field) field.classList.remove('invalid');
        if (msg) msg.textContent = '';
    }

    // Real-time validation on blur
    document.getElementById('full-name')?.addEventListener('blur', function () {
        const val = this.value.trim();
        if (!val) setFieldError('full-name', 'name-msg', 'Full name is required.');
        else if (val.length < 2) setFieldError('full-name', 'name-msg', 'Name must be at least 2 characters.');
        else if (!/^[a-zA-Z\s.'-]+$/.test(val)) setFieldError('full-name', 'name-msg', 'Name contains invalid characters.');
        else clearFieldError('full-name', 'name-msg');
    });

    document.getElementById('email')?.addEventListener('blur', function () {
        const val = this.value.trim();
        const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!val) setFieldError('email', 'email-msg', 'Email is required.');
        else if (!emailRe.test(val)) setFieldError('email', 'email-msg', 'Please enter a valid email address.');
        else clearFieldError('email', 'email-msg');
    });

    document.getElementById('phone')?.addEventListener('blur', function () {
        const val = this.value.trim();
        const phoneRe = /^[+]?[0-9\s\-]{10,15}$/;
        if (!val) setFieldError('phone', 'phone-msg', 'Phone number is required.');
        else if (!phoneRe.test(val)) setFieldError('phone', 'phone-msg', 'Enter a valid 10-15 digit phone number.');
        else clearFieldError('phone', 'phone-msg');
    });

    // Full form validation
    function validateForm() {
        let valid = true;

        // Full Name
        const name = document.getElementById('full-name')?.value.trim();
        if (!name || name.length < 2 || !/^[a-zA-Z\s.'-]+$/.test(name)) {
            setFieldError('full-name', 'name-msg', 'Please enter your full name (letters only).');
            valid = false;
        } else clearFieldError('full-name', 'name-msg');

        // Department
        const dept = document.getElementById('department')?.value;
        if (!dept) { setFieldError('department', 'dept-msg', 'Please select your department.'); valid = false; }
        else clearFieldError('department', 'dept-msg');

        // Year
        const year = document.getElementById('year')?.value;
        if (!year) { setFieldError('year', 'year-msg', 'Please select your academic year.'); valid = false; }
        else clearFieldError('year', 'year-msg');

        // Email
        const email = document.getElementById('email')?.value.trim();
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            setFieldError('email', 'email-msg', 'Please enter a valid email address.'); valid = false;
        } else clearFieldError('email', 'email-msg');

        // Phone
        const phone = document.getElementById('phone')?.value.trim();
        if (!phone || !/^[+]?[0-9\s\-]{10,15}$/.test(phone)) {
            setFieldError('phone', 'phone-msg', 'Please enter a valid phone number.'); valid = false;
        } else clearFieldError('phone', 'phone-msg');

        // Interest
        const interest = document.getElementById('interest')?.value;
        if (!interest) { setFieldError('interest', 'interest-msg', 'Please select your area of interest.'); valid = false; }
        else clearFieldError('interest', 'interest-msg');

        // Checkboxes
        const oath = document.getElementById('accept-oath')?.checked;
        const terms = document.getElementById('accept-terms')?.checked;
        const oathLabel = document.getElementById('oath-label');
        const termsLabel = document.getElementById('terms-label');

        if (!oath) { oathLabel?.classList.add('invalid-check'); valid = false; }
        else oathLabel?.classList.remove('invalid-check');

        if (!terms) { termsLabel?.classList.add('invalid-check'); valid = false; }
        else termsLabel?.classList.remove('invalid-check');

        return valid;
    }

    // Form submission
    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        if (!validateForm()) {
            // Scroll to first error
            const firstErr = form.querySelector('.invalid, .invalid-check');
            if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }

        const btn = document.getElementById('submit-btn');
        const btnText = document.getElementById('btn-text');
        const btnLoad = document.getElementById('btn-loader');
        const successEl = document.getElementById('form-success');
        const errorEl = document.getElementById('form-error');
        const errorMsg = document.getElementById('error-msg');

        // Show loading state
        btn.disabled = true;
        btnText.style.display = 'none';
        btnLoad.style.display = 'inline';
        successEl.style.display = 'none';
        errorEl.style.display = 'none';

        // Build payload (sanitized)
        const payload = {
            full_name: sanitize(document.getElementById('full-name').value.trim()),
            department: sanitize(document.getElementById('department').value),
            year: sanitize(document.getElementById('year').value),
            email: sanitize(document.getElementById('email').value.trim()),
            phone: sanitize(document.getElementById('phone').value.trim()),
            skills: sanitize(document.getElementById('skills').value.trim()),
            interest: sanitize(document.getElementById('interest').value),
            accept_oath: true,
            accept_terms: true
        };

        try {
            const response = await fetch(`${BACKEND_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                successEl.style.display = 'flex';
                form.reset();
                form.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                errorMsg.textContent = data.message || 'Registration failed. Please try again.';
                errorEl.style.display = 'flex';
            }

        } catch (err) {
            // Backend not reachable — show helpful message
            errorMsg.textContent = 'Cannot connect to the server. If running locally, make sure the Flask backend is running (python backend/app.py).';
            errorEl.style.display = 'flex';
        } finally {
            btn.disabled = false;
            btnText.style.display = 'inline';
            btnLoad.style.display = 'none';
        }
    });
})();


/* ============================================================
   9. ACTIVE NAV LINK HIGHLIGHTING
   ============================================================ */
(function setActiveNavLink() {
    const path = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-links a, .mobile-nav a').forEach(link => {
        const href = link.getAttribute('href');
        if (href === path || (path === '' && href === 'index.html')) {
            link.classList.add('active');
        }
    });
})();


/* ============================================================
   10. SMOOTH ANCHOR SCROLLING
   ============================================================ */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (!target) return;
        e.preventDefault();
        const offset = 80; // navbar height
        window.scrollTo({ top: target.offsetTop - offset, behavior: 'smooth' });
    });
});


/* ============================================================
   11. FOOTER CURRENT YEAR
   ============================================================ */
document.querySelectorAll('.footer-year').forEach(el => {
    el.textContent = new Date().getFullYear();
});


/* ============================================================
   12. LAUNCH COUNTDOWN TIMER (March 10, 2026)
   ============================================================ */
(function initCountdown() {
    const wrap = document.getElementById('countdown-wrap');
    if (!wrap) return;

    // Launch date: March 10, 2026 at 00:00:00 IST (UTC+5:30)
    const LAUNCH = new Date('2026-03-10T00:00:00+05:30').getTime();

    const elDays = document.getElementById('cd-days');
    const elHours = document.getElementById('cd-hours');
    const elMins = document.getElementById('cd-mins');
    const elSecs = document.getElementById('cd-secs');

    function pad(n) { return String(n).padStart(2, '0'); }

    function tick(el, val) {
        const prev = el.textContent;
        if (prev !== val) {
            el.classList.remove('tick');
            void el.offsetWidth; // reflow
            el.classList.add('tick');
            el.textContent = val;
            setTimeout(() => el.classList.remove('tick'), 200);
        }
    }

    function update() {
        const now = Date.now();
        const diff = LAUNCH - now;

        if (diff <= 0) {
            // Club has launched!
            wrap.classList.add('launched');
            wrap.innerHTML = `
                <div class="launched-msg">🎉 CSSC IS OFFICIALLY LAUNCHED! 🎉</div>
                <div class="countdown-date">📅 Established March 10, 2026</div>
            `;
            return; // stop ticking
        }

        const days = Math.floor(diff / 86400000);
        const hours = Math.floor((diff % 86400000) / 3600000);
        const mins = Math.floor((diff % 3600000) / 60000);
        const secs = Math.floor((diff % 60000) / 1000);

        tick(elDays, pad(days));
        tick(elHours, pad(hours));
        tick(elMins, pad(mins));
        tick(elSecs, pad(secs));

        setTimeout(update, 1000);
    }

    update();
})();
