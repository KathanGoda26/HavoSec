import React, { useState } from 'react'
import SEO from '@/components/SEO'
import LuxuryButton from '@/components/LuxuryButton'

const postsData = [
  { id: 1, title: 'The Rise of AI-Powered Cyber Attacks in 2024', excerpt: 'Explore how artificial intelligence is being weaponized by threat actors and what organizations can do to defend against these sophisticated attacks.', author: 'Dr. Sarah Chen', publishedDate: '2024-12-15', readTime: '8 min read', image: 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=600&h=400&fit=crop', tags: ['AI Security', 'Threat Intelligence', 'Research'] },
  { id: 2, title: 'Zero Trust Architecture: A Complete Implementation Guide', excerpt: 'Learn how to implement a zero trust security model from the ground up, including best practices and common pitfalls to avoid.', author: 'James Mitchell', publishedDate: '2024-11-28', readTime: '12 min read', image: 'https://images.unsplash.com/photo-1563986768609-322da13575f2?w=600&h=400&fit=crop', tags: ['Zero Trust', 'Architecture', 'Best Practices'] },
  { id: 3, title: 'Critical Vulnerability in Popular Enterprise Software', excerpt: 'A deep dive into the recently discovered CVE affecting millions of enterprise installations and the steps needed to mitigate the risk.', author: 'Alex Rivera', publishedDate: '2024-11-10', readTime: '6 min read', image: 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&h=400&fit=crop', tags: ['CVE', 'Vulnerability', 'Enterprise'] },
  { id: 4, title: 'Building a Security Operations Center on a Budget', excerpt: 'Practical strategies for startups and SMBs to establish effective security monitoring without breaking the bank.', author: 'Maria Gonzalez', publishedDate: '2024-10-22', readTime: '10 min read', image: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=600&h=400&fit=crop', tags: ['SOC', 'Budget', 'Startups'] },
  { id: 5, title: 'Ransomware Trends: What to Expect in 2025', excerpt: 'An analysis of evolving ransomware tactics and the emerging defensive strategies organizations should adopt.', author: 'Dr. Sarah Chen', publishedDate: '2024-10-05', readTime: '9 min read', image: 'https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=600&h=400&fit=crop', tags: ['Ransomware', 'Trends', 'Defense'] },
  { id: 6, title: 'Cloud Security Best Practices for Multi-Cloud Environments', excerpt: 'Navigate the complexities of securing workloads across AWS, Azure, and GCP with these proven strategies.', author: 'James Mitchell', publishedDate: '2024-09-18', readTime: '11 min read', image: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=400&fit=crop', tags: ['Cloud Security', 'Multi-Cloud', 'DevSecOps'] },
]

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

function Blog() {
  const [email, setEmail] = useState('')
  const [subscribing, setSubscribing] = useState(false)

  const readPost = (post) => console.log('Reading post:', post.title)

  const subscribeNewsletter = (e) => {
    e.preventDefault()
    if (!email) return
    setSubscribing(true)
    setTimeout(() => { console.log('Subscribed:', email); setEmail(''); setSubscribing(false) }, 1500)
  }

  return (
    <div className="blog-page">
      <SEO title="Security Insights & Updates" description="Stay informed with the latest cybersecurity trends and threat analysis." />
      <div className="container">
        <section className="blog-hero" data-testid="blog-hero">
          <h1 className="heading-luxury">Security Insights & Updates</h1>
          <p className="hero-subtitle">Stay informed with the latest cybersecurity trends, threat analysis, and best practices from our security experts</p>
        </section>

        <section className="blog-posts" data-testid="blog-posts">
          <div className="posts-grid">
            {postsData.map(post => (
              <article key={post.id} className="post-card glass" onClick={() => readPost(post)} data-testid={`blog-post-${post.id}`}>
                <div className="post-image">
                  <img src={post.image} alt={post.title} />
                  <div className="post-overlay"><span className="read-time">{post.readTime}</span></div>
                </div>
                <div className="post-content">
                  <div className="post-meta">
                    <span className="post-author">{post.author}</span>
                    <span className="post-date">{formatDate(post.publishedDate)}</span>
                  </div>
                  <h2 className="post-title">{post.title}</h2>
                  <p className="post-excerpt">{post.excerpt}</p>
                  <div className="post-tags">
                    {post.tags.map(tag => <span key={tag} className="tag">{tag}</span>)}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="newsletter-section glass" data-testid="newsletter-section">
          <div className="newsletter-content">
            <h2 className="newsletter-title">Stay Updated</h2>
            <p className="newsletter-description">Get the latest security insights and threat updates delivered to your inbox</p>
            <form onSubmit={subscribeNewsletter} className="newsletter-form">
              <input value={email} onChange={e => setEmail(e.target.value)} type="email" placeholder="Enter your email address" required className="newsletter-input" data-testid="newsletter-email-input" />
              <LuxuryButton type="submit" loading={subscribing} data-testid="newsletter-subscribe-button">Subscribe</LuxuryButton>
            </form>
          </div>
        </section>
      </div>
    </div>
  )
}

export default Blog
