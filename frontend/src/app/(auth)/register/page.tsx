export default function RegisterPage() {
  return (
    <main className="authPage">
      <form className="authCard">
        <p className="eyebrow">Paper trading setup</p>
        <h1>Create account</h1>
        <label>
          Full name
          <input type="text" placeholder="Alex Investor" />
        </label>
        <label>
          Email
          <input type="email" placeholder="you@example.com" />
        </label>
        <label>
          Password
          <input type="password" placeholder="Create a password" />
        </label>
        <button type="submit" className="button primary">
          Register
        </button>
      </form>
    </main>
  );
}
