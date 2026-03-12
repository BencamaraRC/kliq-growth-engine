interface StepProgressProps {
  steps: string[]
  current: number
}

export function StepProgress({ steps, current }: StepProgressProps) {
  return (
    <div className="flex items-center justify-center w-full">
      {steps.map((label, i) => {
        const isCompleted = i < current
        const isActive = i === current

        return (
          <div key={label} className="flex items-center">
            {/* Step circle + label */}
            <div className="flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold border-2 transition-all ${
                  isCompleted
                    ? 'bg-kliq-green border-kliq-green text-white'
                    : isActive
                      ? 'bg-white border-kliq-green text-kliq-green'
                      : 'bg-white border-gray-300 text-gray-400'
                }`}
              >
                {isCompleted ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              <span
                className={`mt-2 text-xs font-medium whitespace-nowrap ${
                  isCompleted || isActive ? 'text-kliq-green' : 'text-gray-400'
                }`}
              >
                {label}
              </span>
            </div>

            {/* Connecting line */}
            {i < steps.length - 1 && (
              <div
                className={`w-16 h-0.5 mx-2 mb-6 ${
                  isCompleted ? 'bg-kliq-green' : 'bg-gray-300'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
