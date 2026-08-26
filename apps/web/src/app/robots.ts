import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: [
        "/",
        "/how-it-works",
        "/security",
        "/docs",
        "/pricing",
        "/faq",
        "/contact",
        "/privacy",
        "/terms",
      ],
      disallow: ["/api/", "/jobs/*", "/repositories/*", "/settings"],
    },
    sitemap: "https://patchproof.dev/sitemap.xml",
  };
}
