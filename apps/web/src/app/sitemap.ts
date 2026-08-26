import { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = "https://patchproof.dev";
  const routes = [
    "",
    "/how-it-works",
    "/security",
    "/docs",
    "/pricing",
    "/faq",
    "/contact",
    "/privacy",
    "/terms",
  ];

  return routes.map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: route === "" ? "daily" : "weekly",
    priority: route === "" ? 1.0 : route === "/security" || route === "/docs" ? 0.9 : 0.8,
  }));
}
