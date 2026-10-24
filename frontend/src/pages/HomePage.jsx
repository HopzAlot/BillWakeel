
import { Link } from "react-router-dom";

function HomePage() {
  return (
    <main className="home-page">
      <section className="hero">
        <p className="eyebrow">A MORE THOUGHTFUL WAY TO REVIEW YOUR BILLS</p>

        <h1>
          Every charge
          <br />
          deserves a <span>closer look.</span>
        </h1>

        <p className="hero-description">
          Utility bills shouldn't feel like a guessing game. BillWakeel helps
          you review the details, understand the charges, and spot items that
          may need a second look.
        </p>

        <div className="hero-actions">
          <Link to="/upload" className="primary-button">
            Review a bill <span aria-hidden="true">↗</span>
          </Link>

          <span className="hero-note">Your bill. Your review. Your decision.</span>
        </div>
      </section>

      <section className="feature-grid" aria-label="How BillWakeel helps">
        <article className="feature-card">
          <span className="feature-number">01 / READ</span>
          <h2>Bring the details into focus.</h2>
          <p>
            Start with a bill image or PDF and review the information extracted
            from it.
          </p>
        </article>

        <article className="feature-card">
          <span className="feature-number">02 / REVIEW</span>
          <h2>Know what to double-check.</h2>
          <p>
            Examine charges and values that may need your attention before
            taking the next step.
          </p>
        </article>

        <article className="feature-card">
          <span className="feature-number">03 / DECIDE</span>
          <h2>Stay in control.</h2>
          <p>
            Review the findings yourself. You decide whether any further action
            is needed.
          </p>
        </article>
      </section>

      <footer className="home-footer">
        <span>BUILT FOR CLARITY</span>
        <span>Understand first. Act with confidence.</span>
      </footer>
    </main>
  );
}

export default HomePage;
