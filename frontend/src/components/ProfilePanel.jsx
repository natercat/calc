const LEVEL_LABEL = {
  unknown: 'Not assessed',
  weak: 'Needs work',
  developing: 'Developing',
  strong: 'Strong',
}

const LEVEL_CLASS = {
  unknown: 'level-unknown',
  weak: 'level-weak',
  developing: 'level-developing',
  strong: 'level-strong',
}

export default function ProfilePanel({ profile }) {
  const skills = Object.entries(profile || {})
  return (
    <aside className="profile-panel">
      <h3>Your Skill Profile</h3>
      {skills.length === 0 && <p>No data yet.</p>}
      <ul>
        {skills.map(([skill, level]) => (
          <li key={skill} className={LEVEL_CLASS[level]}>
            <span className="skill-name">{skill.replace(/_/g, ' ')}</span>
            <span className="skill-level">{LEVEL_LABEL[level] || level}</span>
          </li>
        ))}
      </ul>
    </aside>
  )
}
