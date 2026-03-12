import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { fetchBlog, type Blog } from '@/api/blogs'

export function BlogDetailPage() {
  const { id } = useParams<{ id: string }>()
  const {
    data: blog,
    isLoading,
    error,
  } = useQuery<Blog>({
    queryKey: ['blog', id],
    queryFn: () => fetchBlog(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-8 h-8 border-2 border-kliq-green border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !blog) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-20 text-center">
        <h1 className="text-2xl font-bold text-gray-900">Blog post not found</h1>
        <p className="mt-2 text-gray-600">The post you're looking for doesn't exist or has been removed.</p>
        <Link
          to="/blog"
          className="inline-block mt-6 text-sm font-medium text-kliq-green hover:text-kliq-green-hover"
        >
          &larr; Back to all posts
        </Link>
      </div>
    )
  }

  return (
    <article className="max-w-3xl mx-auto px-6 py-16">
      {/* Back link */}
      <Link
        to="/blog"
        className="inline-flex items-center gap-1 text-sm font-medium text-kliq-green hover:text-kliq-green-hover transition-colors mb-8"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Blog
      </Link>

      {/* Tags */}
      {blog.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {blog.tags.map((tag) => (
            <span
              key={tag}
              className="text-xs font-medium text-kliq-green bg-kliq-green-light px-3 py-1 rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Title */}
      <h1 className="text-4xl font-bold text-gray-900 tracking-tight leading-tight">{blog.title}</h1>

      {/* Coach attribution + date */}
      <div className="mt-6 flex items-center gap-3 pb-8 border-b border-gray-200">
        {blog.coach_image ? (
          <img
            src={blog.coach_image}
            alt={blog.coach_name}
            className="w-10 h-10 rounded-full object-cover"
          />
        ) : (
          <div className="w-10 h-10 rounded-full bg-kliq-green/10 flex items-center justify-center">
            <span className="text-sm font-semibold text-kliq-green">
              {blog.coach_name?.[0]?.toUpperCase()}
            </span>
          </div>
        )}
        <div>
          <div className="text-sm font-medium text-gray-900">{blog.coach_name}</div>
          {blog.published_at && (
            <div className="text-xs text-gray-500">
              {new Date(blog.published_at).toLocaleDateString('en-US', {
                month: 'long',
                day: 'numeric',
                year: 'numeric',
              })}
            </div>
          )}
        </div>
      </div>

      {/* Body */}
      <div
        className="mt-8 prose prose-gray prose-lg max-w-none prose-headings:text-gray-900 prose-a:text-kliq-green"
        dangerouslySetInnerHTML={{ __html: blog.body_html || '' }}
      />
    </article>
  )
}
