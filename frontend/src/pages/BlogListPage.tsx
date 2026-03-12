import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchBlogs, type Blog } from '@/api/blogs'

export function BlogListPage() {
  const { data: blogs, isLoading, error } = useQuery<Blog[]>({
    queryKey: ['blogs'],
    queryFn: fetchBlogs,
  })

  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 tracking-tight">Blog</h1>
        <p className="mt-3 text-gray-600 max-w-xl mx-auto">
          Expert insights, tips, and strategies from top fitness and wellness coaches.
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-2 border-kliq-green border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <div className="text-center py-20">
          <p className="text-red-600">Failed to load blog posts. Please try again later.</p>
        </div>
      )}

      {blogs && blogs.length === 0 && (
        <div className="text-center py-20">
          <p className="text-gray-500">No blog posts yet. Check back soon!</p>
        </div>
      )}

      {blogs && blogs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {blogs.map((blog) => (
            <Link
              key={blog.id}
              to={`/blog/${blog.id}`}
              className="group bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg hover:border-kliq-green/30 transition-all"
            >
              {/* Placeholder image */}
              <div className="h-48 bg-gradient-to-br from-kliq-green-light to-kliq-green/10 flex items-center justify-center">
                <svg
                  className="w-12 h-12 text-kliq-green/30"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
                  />
                </svg>
              </div>

              <div className="p-5">
                {/* Tags */}
                {blog.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {blog.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="text-xs font-medium text-kliq-green bg-kliq-green-light px-2 py-0.5 rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                <h2 className="text-lg font-semibold text-gray-900 group-hover:text-kliq-green transition-colors line-clamp-2">
                  {blog.title}
                </h2>
                <p className="mt-2 text-sm text-gray-600 line-clamp-3">{blog.excerpt}</p>

                {/* Coach attribution */}
                <div className="mt-4 flex items-center gap-2">
                  {blog.coach_image ? (
                    <img
                      src={blog.coach_image}
                      alt={blog.coach_name}
                      className="w-6 h-6 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-kliq-green/10 flex items-center justify-center">
                      <span className="text-xs font-medium text-kliq-green">
                        {blog.coach_name?.[0]?.toUpperCase()}
                      </span>
                    </div>
                  )}
                  <span className="text-xs text-gray-500">{blog.coach_name}</span>
                  {blog.published_at && (
                    <>
                      <span className="text-xs text-gray-300">·</span>
                      <span className="text-xs text-gray-500">
                        {new Date(blog.published_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
