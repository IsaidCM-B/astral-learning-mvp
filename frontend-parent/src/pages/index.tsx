import { GetServerSideProps } from 'next';
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuthStore } from '@/stores/auth.store';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { OverviewCard } from '@/components/dashboard/OverviewCard';
import { ProgressChart } from '@/components/dashboard/ProgressChart';
import { RecentActivity } from '@/components/dashboard/RecentActivity';
import { QuickActions } from '@/components/dashboard/QuickActions';

interface HomePageProps {
  user?: {
    id: string;
    email: string;
    role: string;
    profile: {
      firstName: string;
      lastName: string;
    };
  };
}

export default function HomePage({ user: serverUser }: HomePageProps) {
  const router = useRouter();
  const { user, setUser, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (serverUser) {
      setUser(serverUser);
    } else if (!isAuthenticated) {
      router.push('/login');
    }
  }, [serverUser, setUser, isAuthenticated, router]);

  if (!isAuthenticated) {
    return <div>Loading...</div>;
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="border-b border-gray-200 pb-5">
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user?.profile?.firstName}!
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Here's what's happening with your child's learning journey.
          </p>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <OverviewCard
            title="Active Missions"
            value="3"
            change="+1 from last week"
            changeType="increase"
            icon="mission"
          />
          <OverviewCard
            title="Learning Hours"
            value="12.5"
            change="+2.3 from last week"
            changeType="increase"
            icon="time"
          />
          <OverviewCard
            title="Achievement Points"
            value="450"
            change="+50 from last week"
            changeType="increase"
            icon="trophy"
          />
          <OverviewCard
            title="Completion Rate"
            value="87%"
            change="+5% from last week"
            changeType="increase"
            icon="chart"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Progress Chart */}
          <div className="lg:col-span-2">
            <ProgressChart />
          </div>

          {/* Quick Actions */}
          <div>
            <QuickActions />
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <RecentActivity />
        </div>
      </div>
    </DashboardLayout>
  );
}

export const getServerSideProps: GetServerSideProps = async (context) => {
  // Check authentication
  const token = context.req.cookies.auth_token;
  
  if (!token) {
    return {
      props: {},
      redirect: {
        destination: '/login',
        permanent: false,
      },
    };
  }

  try {
    // Validate token and get user data
    // This would be an API call to your backend
    const user = {
      id: 'user-id',
      email: 'parent@example.com',
      role: 'parent',
      profile: {
        firstName: 'John',
        lastName: 'Doe',
      },
    };

    return {
      props: { user },
    };
  } catch (error) {
    return {
      props: {},
      redirect: {
        destination: '/login',
        permanent: false,
      },
    };
  }
};
