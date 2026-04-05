export default function LoginPage() {
  return (
    <main className="authPage">
      <form className="authCard">
        <p className="eyebrow">Welcome back</p>
        <h1>Sign in</h1>
        <label>
          Email
          <input type="email" placeholder="you@example.com" />
        </label>
        <label>
          Password
          <input type="password" placeholder="••••••••" />
        </label>
        <button type="submit" className="button primary">
          Sign in
        </button>
      </form>
    </main>
  );
}
