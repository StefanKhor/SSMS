<template>
  <el-container class="common-layout">
    <el-header>
      <h1>Staff & Shift Management System</h1>
    </el-header>
    <el-main>
      <el-tabs type="border-card">
        <el-tab-pane label="Staff Management">
          <StaffList />
        </el-tab-pane>
        <el-tab-pane label="Schedule">
          <ShiftSchedule ref="shiftScheduleRef"/>
        </el-tab-pane>
        <el-tab-pane label="Auto Scheduling & Export">
          <AdminTools @schedule-complete="handleScheduleComplete"/>
        </el-tab-pane>
      </el-tabs>
    </el-main>
  </el-container>
</template>

<script setup>
import StaffList from './components/StaffList.vue';
import ShiftSchedule from './components/ShiftSchedule.vue';
import AdminTools from './components/AdminTools.vue';

import { ElMessage } from 'element-plus';
import { ref } from 'vue';
const shiftScheduleRef = ref(null);
const handleScheduleComplete = () => {
  if (shiftScheduleRef.value && shiftScheduleRef.value.fetchShifts) {
    shiftScheduleRef.value.fetchShifts();
    ElMessage.success('Schedule refreshed successfully.');
  }
};
</script>

<style>
.common-layout {
  max-width: 1200px;
  margin: 0 auto;
}
.el-header {
  text-align: center;
  padding: 20px 0;
  margin-bottom: 20px
}
.shift-schedule-container .el-calendar__body {
    padding: 12px;
}

* {
  font-family: 'Sans', Tahoma, Geneva, Verdana, sans-serif;
}
</style>