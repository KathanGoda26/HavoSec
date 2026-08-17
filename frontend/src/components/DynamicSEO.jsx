import React, { useEffect, useMemo } from 'react'
import { Helmet } from 'react-helmet-async'
import { useLocation } from 'react-router-dom'
import { useSEOStore } from '@/stores/seoStore'

function DynamicSEO({ page, title = null, description = null, image = null, url = null, type = null, keywords = null }) {
  const location = useLocation()
  const seoStore = useSEOStore()

  useEffect(() => {
    seoStore.fetchGlobalSEO()
    seoStore.fetchPageSEO(page)
  }, [page])

  const pageSEO = seoStore.pageSEO[page] || {}
  const globalSEO = seoStore.globalSEO || {}

  const seoTitle = title || pageSEO.seo?.title || 'HavoSec - Advanced Cybersecurity Platform'
  const seoDescription = description || pageSEO.seo?.description || "Protect your organization with HavoSec's comprehensive cybersecurity solutions."
  const seoKeywords = keywords || pageSEO.seo?.keywords || 'cybersecurity, security platform, threat detection'
  const seoImage = image || pageSEO.seo?.ogImage || globalSEO.defaultOgImage || '/logo1.png'

  const baseUrl = globalSEO.siteUrl || 'https://havosec.com'
  const seoUrl = url || pageSEO.seo?.canonical || `${baseUrl}${location.pathname}`

  const seoType = type || pageSEO.seo?.ogType || 'website'
  const seoRobots = pageSEO.seo?.robots || 'index, follow'
  const seoAuthor = pageSEO.seo?.author || globalSEO.defaultAuthor || 'HavoSec Team'
  const twitterCard = pageSEO.seo?.twitterCard || 'summary_large_image'
  const twitterSite = pageSEO.seo?.twitterSite || globalSEO.twitterSite || '@HavoSec'
  const siteName = globalSEO.siteName || 'HavoSec'
  const themeColor = globalSEO.themeColor || '#8b5cf6'

  const fullTitle = `${seoTitle} | ${siteName}`

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={seoDescription} />
      <meta name="keywords" content={seoKeywords} />
      <meta name="author" content={seoAuthor} />
      <meta name="robots" content={seoRobots} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={seoDescription} />
      <meta property="og:image" content={seoImage} />
      <meta property="og:url" content={seoUrl} />
      <meta property="og:type" content={seoType} />
      <meta property="og:site_name" content={siteName} />
      <meta name="twitter:card" content={twitterCard} />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={seoDescription} />
      <meta name="twitter:image" content={seoImage} />
      <meta name="twitter:site" content={twitterSite} />
      <meta name="theme-color" content={themeColor} />
      <meta name="msapplication-TileColor" content={themeColor} />
      <link rel="canonical" href={seoUrl} />
    </Helmet>
  )
}

export default DynamicSEO
