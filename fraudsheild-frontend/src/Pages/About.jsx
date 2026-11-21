import { Link } from "react-router-dom";

const PRINCIPLES = [
  ["Show the reasons", "A score alone isn’t enough. We mark the exact phrases and facts behind every result, so you learn what scams look like."],
  ["Use plain words", "No security jargon. Every result ends with what to do next: ignore it, confirm it, or report it."],
  ["Warn each other", "Every report you file helps others recognise the same scam sooner."],
];

const FAQ = [
  ["Is my message saved?", "In this demo, checks stay in your browser tab and disappear when you reload."],
  ["Can FraudSheild be wrong?", "Yes. It gives guidance, not a guarantee. A low score doesn’t prove a message is safe."],
  ["I already lost money. What now?", "Contact your bank straight away and report the scam to the relevant authority in your country."],
];

export default function About() {
  return (
    <main className="mx-auto max-w-6xl px-4 pb-16 pt-8 md:px-10">
      <h1 className="font-display max-w-3xl text-4xl font-bold leading-tight tracking-tight md:text-5xl">
        We help people spot scams before they cost anything.
      </h1>
      <p className="mt-4 max-w-[60ch] text-lg opacity-70">
        Checkpoint started from a simple idea: when a strange message arrives, you shouldn’t have to guess. You should be able to check it in seconds and see why it looks wrong.
      </p>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        {PRINCIPLES.map(([title, text]) => (
          <div key={title} className="card border border-base-300 bg-base-100"><div className="card-body">
            <h3 className="font-display text-base font-bold">{title}</h3>
            <p className="text-sm opacity-70">{text}</p>
          </div></div>
        ))}
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-[1.1fr_.9fr]">
        <div className="card border border-base-300 bg-base-100"><div className="card-body">
          <h2 className="font-display text-lg font-bold">Common questions</h2>
          <div className="mt-2 grid gap-2">
            {FAQ.map(([q, a]) => (
              <div key={q} className="collapse collapse-arrow border border-base-300 bg-base-200">
                <input type="checkbox" aria-label={q} />
                <div className="collapse-title font-semibold">{q}</div>
                <div className="collapse-content text-sm opacity-80"><p>{a}</p></div>
              </div>
            ))}
          </div>
        </div></div>

        <div className="card border border-base-300 bg-base-100"><div className="card-body">
          <h2 className="font-display text-lg font-bold">Get in touch</h2>
          <p className="text-sm opacity-70">Questions, feedback, or a scam pattern we should know about? Write to us.</p>
          <p className="font-semibold">hello@fraudsheild.example</p>
          <Link to="/reports" className="btn btn-primary mt-2 w-fit text-white">Report a scam</Link>
        </div></div>
      </div>
    </main>
  );
}