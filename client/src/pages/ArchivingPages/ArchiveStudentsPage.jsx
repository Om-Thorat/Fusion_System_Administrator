import React, { useState, useMemo, useEffect } from "react";
import {
    Tabs, Card, Text, ScrollArea, Container, Title,
    Flex, Button, TextInput, MultiSelect, Grid, Loader,
    Paper, Center, Divider, Checkbox, Group,
    rem, Modal
} from "@mantine/core";
import { debounce } from "lodash";
import { showNotification } from "@mantine/notifications";
import { FaCheck, FaTimes } from "react-icons/fa";
import { bulkArchiveStudents, getArchiveRecords, unarchiveStudent, viewArchive } from "../../api/Archive";
import { fetchUsersByType } from "../../api/Users";

const InfoCard = ({ person, selectable, selected, onSelectChange, onClick, showUnarchive, onUnarchive, unarchiveLoading }) => (
    <Card
        shadow="sm"
        radius="xl"
        withBorder
        p="lg"
        style={{ backgroundColor: "#fdfdfd", cursor: onClick ? "pointer" : "default" }}
        onClick={onClick}
    >
        <Group position="apart" align="flex-start">
            <div style={{ flex: 1 }}>
                <Text fw={600} size="lg" mb="xs">{person.full_name}</Text>
                <Text size="sm" c="dimmed"><strong>Username:</strong> {person.username}</Text>
                <Divider my="sm" />
                <Text size="sm"><strong>Programme:</strong> {person.programme || "-"}</Text>
                <Text size="sm"><strong>Discipline:</strong> {person.discipline || "-"}</Text>
                <Text size="sm"><strong>Batch:</strong> {person.batch || "-"}</Text>
                {person.curr_semester_no !== undefined && (
                    <Text size="sm"><strong>Semester:</strong> {person.curr_semester_no}</Text>
                )}
                {person.category && <Text size="sm"><strong>Category:</strong> {person.category}</Text>}
                {person.gender && <Text size="sm"><strong>Gender:</strong> {person.gender}</Text>}
            </div>
            {selectable && (
                <Checkbox
                    checked={selected}
                    onChange={() => onSelectChange(person.username)}
                    mt="sm"
                />
            )}
            {showUnarchive && (
                <Button
                    size="xs"
                    color="red"
                    variant="light"
                    loading={unarchiveLoading}
                    onClick={(event) => {
                        event.stopPropagation();
                        onUnarchive(person.username);
                    }}
                    mt="sm"
                >
                    Unarchive
                </Button>
            )}
        </Group>
    </Card>
);

const extractUnique = (arr, key) =>
    [...new Set(arr.map((item) => key === "semester"
        ? String(item.curr_semester_no)
        : String(item[key] ?? "")
    ).filter(Boolean))];

const filterAndSearch = (data, filters, searchQuery) =>
    data.filter((person) => {
        const fullName = String(person.full_name || "").toLowerCase();
        const username = String(person.username || "").toLowerCase();
        const query = String(searchQuery || "").toLowerCase();

        const matchSearch = fullName.includes(query) || username.includes(query);

        const matchFilters = Object.entries(filters).every(([key, values]) => {
            if (values.length === 0) return true;
            const value = key === "semester"
                ? String(person.curr_semester_no ?? "")
                : String(person[key] ?? "");
            return values.includes(value);
        });

        return matchSearch && matchFilters;
    });

    const getLatestRecordMap = (records) => {
        const map = new Map();
        records.forEach((record) => {
            if (!map.has(record.student_username)) {
                map.set(record.student_username, record);
            }
        });
        return map;
    };

const ArchiveStudentPage = () => {
    const checkIcon = <FaCheck style={{ width: rem(20), height: rem(20) }} />;
    const xIcon = <FaTimes style={{ width: rem(20), height: rem(20) }} />;

        const [students, setStudents] = useState([]);
        const [archiveRecords, setArchiveRecords] = useState([]);
        const [loadingStudents, setLoadingStudents] = useState(true);
        const [loadingRecords, setLoadingRecords] = useState(true);
    const [activeTab, setActiveTab] = useState("archive");
    const [searchQuery, setSearchQuery] = useState("");
    const [filters, setFilters] = useState({
        programme: [], discipline: [], batch: [], category: [], semester: [], gender: []
    });
    const [selectedUsernames, setSelectedUsernames] = useState([]);
    const [modalOpened, setModalOpened] = useState(false);
    const [submittingArchive, setSubmittingArchive] = useState(false);
    const [unarchivingUsername, setUnarchivingUsername] = useState("");
    const [unarchiveModalOpened, setUnarchiveModalOpened] = useState(false);
    const [unarchiveTargetUsername, setUnarchiveTargetUsername] = useState("");
    const [archivedSearchQuery, setArchivedSearchQuery] = useState("");
    const [viewerModalOpened, setViewerModalOpened] = useState(false);
    const [viewerLoading, setViewerLoading] = useState(false);
    const [viewerUsername, setViewerUsername] = useState("");
    const [viewerData, setViewerData] = useState(null);

    const handleSearchChange = useMemo(() =>
        debounce((value) => setSearchQuery(value), 200), []);

    const loadStudents = async () => {
        setLoadingStudents(true);
        try {
            const response = await fetchUsersByType("student");
            setStudents(Array.isArray(response) ? response : []);
        } catch (error) {
            setStudents([]);
            showNotification({
                icon: xIcon,
                title: "Failed",
                position: "top-center",
                withCloseButton: true,
                autoClose: 5000,
                message: error.response?.data?.error || "Unable to load students.",
                color: "red",
            });
        } finally {
            setLoadingStudents(false);
        }
    };

    const loadArchiveRecords = async () => {
        setLoadingRecords(true);
        try {
            const response = await getArchiveRecords();
            setArchiveRecords(Array.isArray(response) ? response : []);
        } catch (error) {
            setArchiveRecords([]);
            showNotification({
                icon: xIcon,
                title: "Failed",
                position: "top-center",
                withCloseButton: true,
                autoClose: 5000,
                message: error.response?.data?.error || "Unable to load archive records.",
                color: "red",
            });
        } finally {
            setLoadingRecords(false);
        }
    };

    useEffect(() => {
        loadStudents();
        loadArchiveRecords();
    }, []);

    useEffect(() => {
        return () => {
            handleSearchChange.cancel();
        };
    }, [handleSearchChange]);

    const latestRecordMap = useMemo(() => getLatestRecordMap(archiveRecords), [archiveRecords]);

    const archiveCandidates = useMemo(
        () => students.filter((student) => !latestRecordMap.has(student.username)),
        [students, latestRecordMap],
    );

    const archivedStudents = useMemo(
        () => Array.from(latestRecordMap.values()).filter((record) => record.archive_type === "archived"),
        [latestRecordMap],
    );

    const filteredArchivedStudents = useMemo(() => {
        const query = String(archivedSearchQuery || "").toLowerCase();
        if (!query) return archivedStudents;
        return archivedStudents.filter((student) => {
            const username = String(student.student_username || "").toLowerCase();
            const fullName = String(student.full_name || "").toLowerCase();
            return username.includes(query) || fullName.includes(query);
        });
    }, [archivedStudents, archivedSearchQuery]);

    const filteredData = useMemo(() =>
        filterAndSearch(archiveCandidates, filters, searchQuery),
        [archiveCandidates, filters, searchQuery]
    );

    const isSelected = (username) => selectedUsernames.includes(username);
    const toggleSelect = (username) => {
        setSelectedUsernames((prev) =>
            prev.includes(username) ? prev.filter(u => u !== username) : [...prev, username]
        );
    };

    const selectAll = () => {
        setSelectedUsernames(filteredData.map(u => u.username));
    };

    const clearSelection = () => setSelectedUsernames([]);

    const handleArchiveAction = () => {
        setModalOpened(true);
    };

    const openUnarchiveModal = (username) => {
        setUnarchiveTargetUsername(username);
        setUnarchiveModalOpened(true);
    };

    const confirmUnarchive = async () => {
        if (!unarchiveTargetUsername) return;
        setUnarchivingUsername(unarchiveTargetUsername);
        try {
            await unarchiveStudent(unarchiveTargetUsername);
            showNotification({
                icon: checkIcon,
                title: "Success",
                position: "top-center",
                withCloseButton: true,
                autoClose: 5000,
                message: `${unarchiveTargetUsername} has been unarchived successfully.`,
                color: "green",
            });
            await loadArchiveRecords();
            setUnarchiveModalOpened(false);
            setUnarchiveTargetUsername("");
        } catch (error) {
            showNotification({
                icon: xIcon,
                title: "Unarchive Failed",
                position: "top-center",
                withCloseButton: true,
                autoClose: 5000,
                message: error.response?.data?.error || "Failed to unarchive student.",
                color: "red",
            });
        } finally {
            setUnarchivingUsername("");
        }
    };

    const handleOpenArchivedViewer = async (username) => {
        setViewerLoading(true);
        setViewerUsername(username);
        setViewerModalOpened(true);

        try {
            const response = await viewArchive(username);
            setViewerData(response.data || null);
        } catch (error) {
            setViewerData(null);
            showNotification({
                icon: xIcon,
                title: "Failed to load archive",
                position: "top-center",
                withCloseButton: true,
                autoClose: 5000,
                message: error.response?.data?.error || "Unable to fetch archived data.",
                color: "red",
            });
        } finally {
            setViewerLoading(false);
        }
    };

    const confirmAction = async () => {
        setSubmittingArchive(true);
        const archivedBy =
            localStorage.getItem("username") ||
            localStorage.getItem("loggedInUsername") ||
            "system_admin";

        try {
            const response = await bulkArchiveStudents(
                selectedUsernames,
                "archived",
                archivedBy,
            );

            showNotification({
                icon: checkIcon,
                title: "Success",
                position: "top-center",
                withCloseButton: true,
                autoClose: 5000,
                message: `Archived ${response.success_count || 0} students.`,
                color: "green",
            });
            clearSelection();
            setModalOpened(false);
            await loadArchiveRecords();
        } catch (error) {
            showNotification({
                icon: xIcon,
                title: "Archive Failed",
                position: "top-center",
                withCloseButton: true,
                autoClose: 5000,
                message: error.response?.data?.error || "Failed to archive selected students.",
                color: "red",
            });
        } finally {
            setSubmittingArchive(false);
        }
    };

    return (
        <Container size="lg" py="xl">
            <Flex
                direction={{ base: 'column', sm: 'row' }}
                gap={{ base: 'sm', sm: 'lg' }}
                justify={{ sm: 'center' }}
                mb="xl"
            >
                <Button
                    variant="gradient"
                    size="xl"
                    radius="xs"
                    gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
                    sx={{ display: 'block', width: { base: '100%', sm: 'auto' }, whiteSpace: 'normal', padding: '1rem', textAlign: 'center' }}
                >
                    <Title order={1} sx={{ fontSize: { base: 'lg', sm: 'xl' }, lineHeight: 1.2, wordBreak: 'break-word' }}>
                        Archive Students
                    </Title>
                </Button>
            </Flex>

            <Paper shadow="lg" p="xl" radius="xl" withBorder>
                <Tabs value={activeTab} onChange={setActiveTab} variant="pills" color="blue" radius="lg" keepMounted={false}>
                    <Tabs.List grow mb="lg">
                        <Tabs.Tab value="archive">ARCHIVE</Tabs.Tab>
                        <Tabs.Tab value="archived">ARCHIVED</Tabs.Tab>
                    </Tabs.List>

                    <Tabs.Panel value="archive">
                        <Grid mb="lg">
                            <Grid.Col span={12}>
                                <TextInput
                                    placeholder="🔍 Search students"
                                    radius="md"
                                    onChange={(e) => handleSearchChange(e.currentTarget.value)}
                                />
                            </Grid.Col>
                            {["programme", "discipline", "batch", "semester", "category", "gender"].map((key) => (
                                <Grid.Col span={6} key={key}>
                                    <MultiSelect
                                        label={key[0].toUpperCase() + key.slice(1)}
                                        placeholder={`Filter by ${key}`}
                                        value={filters[key]}
                                        onChange={(value) => setFilters((prev) => ({ ...prev, [key]: value }))}
                                        data={extractUnique(archiveCandidates, key)}
                                        radius="md"
                                        searchable
                                        clearable
                                    />
                                </Grid.Col>
                            ))}
                        </Grid>

                        <Group mb="md">
                            <Button onClick={selectAll} variant="light">Select All</Button>
                            <Button onClick={clearSelection} variant="default">Clear Selection</Button>
                        </Group>

                        <ScrollArea h={400}>
                            <Grid>
                                {(loadingStudents || loadingRecords) ? (
                                    <Grid.Col span={12}>
                                        <Center py="xl">
                                            <Loader />
                                        </Center>
                                    </Grid.Col>
                                ) : filteredData.length === 0 ? (
                                    <Grid.Col span={12}>
                                        <Center py="xl">
                                            <Text c="dimmed">No students available for archiving.</Text>
                                        </Center>
                                    </Grid.Col>
                                ) : (
                                    filteredData.map((student) => (
                                        <Grid.Col span={12} key={student.username}>
                                            <InfoCard
                                                person={student}
                                                selectable
                                                selected={isSelected(student.username)}
                                                onSelectChange={toggleSelect}
                                            />
                                        </Grid.Col>
                                    ))
                                )}
                            </Grid>
                        </ScrollArea>

                        {selectedUsernames.length > 0 && (
                            <Group mt="lg" position="right">
                                <Button color="blue" onClick={handleArchiveAction}>Archive</Button>
                            </Group>
                        )}
                    </Tabs.Panel>

                    <Tabs.Panel value="archived">
                        <Title order={3} mb="md">Recently Archived</Title>
                        <TextInput
                            mb="md"
                            placeholder="Search archived students by username or name"
                            radius="md"
                            value={archivedSearchQuery}
                            onChange={(event) => setArchivedSearchQuery(event.currentTarget.value)}
                        />
                        <Grid>
                            {loadingRecords ? (
                                <Grid.Col span={12}>
                                    <Center py="xl">
                                        <Loader />
                                    </Center>
                                </Grid.Col>
                            ) : filteredArchivedStudents.length === 0 ? (
                                <Grid.Col span={12}>
                                    <Center py="xl">
                                        <Text c="dimmed">No archived students found.</Text>
                                    </Center>
                                </Grid.Col>
                            ) : (
                                filteredArchivedStudents.map((s) => (
                                    <Grid.Col span={12} key={`${s.student_username}-${s.archived_at}`}>
                                        <InfoCard
                                            person={{
                                                username: s.student_username,
                                                full_name: s.full_name,
                                                programme: s.programme,
                                                discipline: s.discipline,
                                                batch: s.batch,
                                            }}
                                            onClick={() => handleOpenArchivedViewer(s.student_username)}
                                            showUnarchive
                                            onUnarchive={openUnarchiveModal}
                                            unarchiveLoading={unarchivingUsername === s.student_username}
                                        />
                                    </Grid.Col>
                                ))
                            )}
                        </Grid>
                    </Tabs.Panel>
                </Tabs>
            </Paper>

            <Modal
                opened={modalOpened}
                onClose={() => setModalOpened(false)}
                title="Confirm Archive"
            >
                <Text size="sm">Are you sure you want to archive the selected students?</Text>
                <Group mt="md" position="right">
                    <Button variant="light" onClick={() => setModalOpened(false)} disabled={submittingArchive}>Cancel</Button>
                    <Button color="blue" onClick={confirmAction} loading={submittingArchive}>Confirm</Button>
                </Group>
            </Modal>

            <Modal
                opened={viewerModalOpened}
                onClose={() => setViewerModalOpened(false)}
                title={`Archived Data: ${viewerUsername}`}
                size="lg"
                centered
            >
                {viewerLoading ? (
                    <Center py="xl">
                        <Loader />
                    </Center>
                ) : viewerData ? (
                    <Grid>
                        {Object.entries(viewerData).map(([field, value]) => (
                            <Grid.Col span={6} key={field}>
                                <Paper withBorder p="sm" radius="md">
                                    <Text size="xs" c="dimmed">{field}</Text>
                                    <Text fw={500}>{value === null || value === "" ? "N/A" : String(value)}</Text>
                                </Paper>
                            </Grid.Col>
                        ))}
                    </Grid>
                ) : (
                    <Text c="dimmed">No archive data found.</Text>
                )}
            </Modal>

            <Modal
                opened={unarchiveModalOpened}
                onClose={() => setUnarchiveModalOpened(false)}
                title="Confirm Unarchive"
                centered
            >
                <Text size="sm">
                    Are you sure you want to unarchive {unarchiveTargetUsername || "this student"}?
                </Text>
                <Group mt="md" position="right">
                    <Button
                        variant="light"
                        onClick={() => setUnarchiveModalOpened(false)}
                        disabled={!!unarchivingUsername}
                    >
                        Cancel
                    </Button>
                    <Button
                        color="red"
                        onClick={confirmUnarchive}
                        loading={!!unarchivingUsername}
                    >
                        Confirm Unarchive
                    </Button>
                </Group>
            </Modal>
        </Container>
    );
};

export default ArchiveStudentPage;