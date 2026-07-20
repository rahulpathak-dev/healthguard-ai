"use client";

import React from "react";

const emergencyNumber = "112";
const topics = [
  ["chest pain", "Call 112 now. Sit still. Do not drive yourself."],
  ["stroke signs", "Call 112 now. Note the time symptoms started. Do not give food or drink."],
  ["severe bleeding", "Call 112 now. Press firmly with clean cloth. Do not remove embedded objects."],
  ["choking", "Call 112 if they cannot breathe, cough, cry, or speak. Do not give water."],
  ["burns", "Cool with running water. Call 112 for large, deep, chemical, electrical, face, or airway burns. Do not use ice."],
  ["poisoning", "Call 112 or a local poison helpline. Keep the container. Do not induce vomiting unless told."],
  ["seizure", "Move hazards away and time it. Call 112 for first, prolonged, repeated, or injury-related seizures."],
  ["fainting", "Lay flat and check breathing. Call 112 for chest pain, injury, seizure, pregnancy, or slow recovery."],
  ["breathing difficulty", "Call 112 now for severe breathing trouble. Sit upright. Do not use someone else's medicine."],
  ["severe allergic reaction", "Call 112 now. Use prescribed epinephrine if available. Do not wait for rash."],
  ["fractures", "Keep still and seek urgent care. Call 112 for major trauma, open fracture, or cold/blue limb."],
  ["unconsciousness", "Call 112 now and check breathing. Do not give food, drink, or medicine."],
];

export function EmergencyGuide() {
  return (
    <section className="emergency-guide-shell">
      <div className="emergency-guide-hero">
        <p className="eyebrow">Rapid emergency guidance for India</p>
        <h1>Call {emergencyNumber} for urgent danger in India.</h1>
        <a className="emergency-call" href={`tel:${emergencyNumber}`}>Call {emergencyNumber}</a>
        <p>112 is India&apos;s national emergency response number. This page is basic first-aid education, not medical care.</p>
      </div>
      <div className="emergency-topic-grid">
        {topics.map(([title, text]) => (
          <article key={title}>
            <h2>{title}</h2>
            <p>{text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
