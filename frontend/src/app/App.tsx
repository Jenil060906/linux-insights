import { MotionConfig } from "framer-motion";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { DashboardPage } from "@/pages/DashboardPage";

function App() {
  return (
    <MotionConfig reducedMotion="user">
      <DashboardLayout>
        <DashboardPage />
      </DashboardLayout>
    </MotionConfig>
  );
}

export default App;
