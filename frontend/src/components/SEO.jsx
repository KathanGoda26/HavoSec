import React from 'react'
import { Helmet } from 'react-helmet-async'

function SEO({ title, description, image = 'https://havosec.com/og-image.jpg', url = 'https://havosec.com', type = 'website', keywords = 'cybersecurity, AI security, threat detection, vulnerability scanning' }) {
  const fullTitle = `HavoSec | ${title}`

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <meta name="author" content="HavoSec Team" />
      <meta name="robots" content="index, follow" />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={image} />
      <meta property="og:url" content={url} />
      <meta property="og:type" content={type} />
      <meta property="og:site_name" content="HavoSec" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={image} />
      <meta name="twitter:site" content="@HavoSec" />
      <meta name="theme-color" content="#8b5cf6" />
      <meta name="msapplication-TileColor" content="#8b5cf6" />
      <link rel="canonical" href={url} />
    </Helmet>
  )
}

export default SEO
