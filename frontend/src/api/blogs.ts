import api from './client'

export interface Blog {
  id: number
  title: string
  excerpt: string
  body_html?: string
  tags: string[]
  seo_title: string
  seo_description: string
  coach_name: string
  coach_image: string | null
  published_at: string | null
}

export const fetchBlogs = () => api.get<Blog[]>('/blogs').then((r) => r.data)

export const fetchBlog = (id: string) => api.get<Blog>(`/blogs/${id}`).then((r) => r.data)
