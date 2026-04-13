import axiosInstance from "../context/axiosInstance";

export const archiveStudent = async (username, archiveType, archivedBy) => {
  try {
    const response = await axiosInstance.post("/archive/student/", {
      username,
      archive_type: archiveType,
      archived_by: archivedBy,
    });
    return response.data;
  } catch (error) {
    console.error("Error archiving student:", error.response?.data || error.message);
    throw error;
  }
};

export const bulkArchiveStudents = async (usernames, archiveType, archivedBy) => {
  try {
    const response = await axiosInstance.post("/archive/bulk/", {
      usernames,
      archive_type: archiveType,
      archived_by: archivedBy,
    });
    return response.data;
  } catch (error) {
    console.error("Error bulk archiving students:", error.response?.data || error.message);
    throw error;
  }
};

export const getArchiveRecords = async () => {
  try {
    const response = await axiosInstance.get("/archive/records/");
    return response.data;
  } catch (error) {
    console.error("Error fetching archive records:", error.response?.data || error.message);
    throw error;
  }
};

export const viewArchive = async (username) => {
  try {
    const response = await axiosInstance.get(`/archive/view/${username}/`);
    return response.data;
  } catch (error) {
    console.error("Error viewing archive:", error.response?.data || error.message);
    throw error;
  }
};

export const unarchiveStudent = async (username) => {
  try {
    const response = await axiosInstance.post("/archive/unarchive/", {
      username,
    });
    return response.data;
  } catch (error) {
    console.error("Error unarchiving student:", error.response?.data || error.message);
    throw error;
  }
};
